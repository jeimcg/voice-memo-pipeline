import whisper
from textblob import TextBlob
import librosa
import matplotlib.pyplot as plt
import numpy as np
import openai
import os
import subprocess
import time
import shutil
import json
from google.cloud import storage
from threading import Thread

# Load configuration from JSON file
CONFIG_FILE = "config.json"

try:
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
except FileNotFoundError:
    print(f"❌ Configuration file {CONFIG_FILE} not found.")
    exit(1)

# Extract configuration parameters
INPUT_BUCKET_NAME = config["input_bucket_name"]
OUTPUT_BUCKET_NAME = config["output_bucket_name"]
INBOX_FOLDER = config["inbox_folder"]
PROCESSED_FOLDER = config["processed_folder"]
ICLOUD_FOLDER = os.path.expanduser(config["icloud_folder"])
LOCAL_WATCH_FOLDER = os.path.expanduser(config["local_watch_folder"])
OPENAI_API_KEY = config["openai_api_key"]
POLL_INTERVAL = config.get("poll_interval", 30)

# Initialize Google Cloud Storage client
storage_client = storage.Client()

# Ensure downloads directory exists
DOWNLOADS_FOLDER = "downloads"
os.makedirs(DOWNLOADS_FOLDER, exist_ok=True)


def is_valid_audio_file(file_name):
    """Checks if a file is a valid audio file (m4a, mp3, wav)."""
    return file_name.lower().endswith((".m4a", ".mp3", ".wav"))


def convert_to_mp3(file_path):
    """Converts an m4a file to mp3 using FFmpeg."""
    if not file_path.endswith(".m4a"):
        return file_path

    output_path = file_path.replace(".m4a", ".mp3")
    print(f"🎵 Converting {file_path} to {output_path}...")
    try:
        subprocess.run(
            ["ffmpeg", "-i", file_path, output_path],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during FFmpeg conversion: {e.stderr}")
        exit(1)

    return output_path


def transcribe_audio(file_path):
    """Transcribes an audio file using OpenAI's Whisper."""
    model = whisper.load_model("base")
    result = model.transcribe(file_path)
    return result["text"]


def analyze_sentiment(text):
    """Analyzes sentiment of the given text using TextBlob."""
    blob = TextBlob(text)
    return {"polarity": blob.sentiment.polarity, "subjectivity": blob.sentiment.subjectivity}


def analyze_with_chatgpt(text):
    """Sends the transcription text to ChatGPT for additional insights."""
    openai.api_key = OPENAI_API_KEY

    prompt = (
        f"Here is a transcription:\n\n{text}\n\n"
        "Please provide:\n"
        "- A summary of the transcription.\n"
        "- Key themes or topics.\n"
        "- Gentle but critical insights to help me reflect further."
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an empathetic and thoughtful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"❌ Error during ChatGPT analysis: {e}")
        return "Unable to analyze transcription with GPT."


def upload_to_gcs(local_path, bucket_name, folder_name):
    """Uploads a file to a specific folder in the GCS bucket."""
    bucket = storage_client.bucket(bucket_name)
    blob_name = folder_name + os.path.basename(local_path)
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(local_path)
    print(f"✅ Uploaded {local_path} to {blob_name}")


def process_and_archive_results(txt_file_path):
    """Archives the .txt results to both GCS and iCloud."""
    upload_to_gcs(txt_file_path, OUTPUT_BUCKET_NAME, PROCESSED_FOLDER)
    cloud_path = os.path.join(ICLOUD_FOLDER, os.path.basename(txt_file_path))
    shutil.copy2(txt_file_path, cloud_path)
    print(f"✅ Copied processed TXT file to iCloud: {cloud_path}")


def save_results(file_path, transcription, sentiment, gpt_insights):
    """Saves transcription, sentiment, and GPT insights to a .txt file."""
    output_dir = "data/processed"
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    output_file = os.path.join(output_dir, f"{base_name}_analysis.txt")

    with open(output_file, "w") as f:
        f.write("Transcription:\n" + transcription + "\n\n")
        f.write(f"Sentiment Analysis:\nPolarity: {sentiment['polarity']}\n")
        f.write(f"Subjectivity: {sentiment['subjectivity']}\n\n")
        f.write("ChatGPT Insights:\n" + gpt_insights)

    return output_file


def process_file(file_path):
    """Processes a single file by running all steps."""
    print(f"🚀 Processing file: {file_path}")

    processed_file = convert_to_mp3(file_path)
    transcription = transcribe_audio(processed_file)
    sentiment = analyze_sentiment(transcription)
    gpt_insights = analyze_with_chatgpt(transcription)

    txt_file_path = save_results(file_path, transcription, sentiment, gpt_insights)
    process_and_archive_results(txt_file_path)

    print(f"✅ Completed processing for {file_path}.")


def watch_local_folder_and_upload():
    """Watches the local symlinked folder and uploads new files to GCS."""
    print(f"📂 Watching {LOCAL_WATCH_FOLDER} for new files...")
    processed_files = set()

    while True:
        try:
            current_files = {f for f in os.listdir(LOCAL_WATCH_FOLDER) if is_valid_audio_file(f)}
            new_files = current_files - processed_files

            for file_name in new_files:
                local_path = os.path.join(LOCAL_WATCH_FOLDER, file_name)
                print(f"📤 Uploading new file: {local_path}")
                upload_to_gcs(local_path, INPUT_BUCKET_NAME, INBOX_FOLDER)
                processed_files.add(file_name)

            time.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            print("🛑 Stopped watching local folder.")
            break


def watch_gcs_polling():
    """Polls the GCS folder and processes new files."""
    print(f"📡 Polling GCS every {POLL_INTERVAL} seconds...")
    processed_files = set()

    while True:
        try:
            bucket = storage_client.bucket(INPUT_BUCKET_NAME)
            blobs = bucket.list_blobs(prefix=INBOX_FOLDER)
            current_files = {blob.name for blob in blobs if not blob.name.endswith('/')}

            new_files = current_files - processed_files
            for file_name in new_files:
                if not is_valid_audio_file(file_name):
                    continue

                local_path = os.path.join(DOWNLOADS_FOLDER, os.path.basename(file_name))
                blob = bucket.blob(file_name)

                try:
                    blob.download_to_filename(local_path)
                    print(f"⬇️ Downloaded {file_name} to {local_path}")
                    process_file(local_path)
                    processed_files.add(file_name)
                except Exception as e:
                    print(f"❌ Error downloading {file_name}: {e}")

            time.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            print("🛑 Stopped polling.")
            break


if __name__ == "__main__":
    # Run both watchers in parallel
    Thread(target=watch_local_folder_and_upload, daemon=True).start()
    watch_gcs_polling()
