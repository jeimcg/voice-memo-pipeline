# Voice Memo Sentiment & Insights Pipeline (DeAlexithyminator - *Demystify Your Emotions*)  

### **Automated voice memo processing with Whisper, NLP sentiment analysis, and cloud storage sync across Google Cloud & iCloud.**  

Originally a project to combat the troubles of exploring mindfulness with journaling in a hyper-focused, fast-paced, and constantly changing world, This project allows users, with a tap of an icon, **to record a voice memo on their phone, automatically upload it to Google Cloud Storage, transcribe it using OpenAI's Whisper, analyze sentiment, and generate critical but gentle insights with ChatGPT**. The results are saved as text files in **Google Cloud Storage and iCloud**, made as intuitively possible by Apple's Shortcut app making them instantly accessible across devices.  

---

## **✨ Features**
✅ **Automated Voice Memo Processing** – Upload voice memos from mobile to Google Cloud automatically.  
✅ **Whisper Transcription** – Converts speech to text with OpenAI's Whisper.  
✅ **Sentiment Analysis** – Uses TextBlob to analyze the emotional tone of the transcript.  
✅ **ChatGPT Insights** – Generates deeper reflections based on the transcription.  
✅ **Google Cloud Storage Sync** – Stores input/output files in cloud storage for accessibility.  
✅ **iCloud Sync** – Stores processed results in iCloud for quick access from mobile.  
✅ **Local Watch Folder** – Supports local-to-cloud syncing using symlinks.  

---

## **🛠️ How It Works**
📱 **1. Record a Voice Memo** → Uploads automatically via iCloud Shortcuts to the **TranscriptionInbox** folder.  
📤 **2. File Syncs to Google Cloud Storage** → A local watcher uploads new files to the **voice-memo-inputs** bucket.  
🎙️ **3. Transcription & Processing** → The script:  
   - Converts M4A files to MP3 (if needed).  
   - Uses Whisper to transcribe the audio.  
   - Runs sentiment analysis & generates ChatGPT insights.  
📄 **4. Stores Results** → Saves transcriptions & analysis in Google Cloud and iCloud for easy access.  

---

## **🛠️ Tech Stack**
- **Python 3.12**  
- **Google Cloud Storage (GCS)**  
- **OpenAI Whisper**  
- **TextBlob (Sentiment Analysis)**  
- **ChatGPT API (Insights Generation)**  
- **FFmpeg (Audio Conversion)**  
- **Librosa (Audio Feature Extraction)**  

---

## **🚀 Setup & Installation**

### **1️⃣ Clone the Repo**
```sh
git clone https://github.com/YOUR_USERNAME/voice-memo-pipeline.git
cd voice-memo-pipeline
```

### **2️⃣ Install Dependencies**
```sh
pip install -r requirements.txt
```

### **3️⃣ Set Up Google Cloud**
Create two GCS Buckets:

voice-memo-inputs (for uploaded voice memos)
voice-memo-outputs (for processed transcriptions)
Create a Service Account, download the JSON key, and authenticate:

```sh
gcloud auth activate-service-account --key-file=your-key.json
Enable required APIs:
```

```sh
gcloud services enable storage.googleapis.com
```

### **4️⃣ Configure Your JSON Settings**
Modify config.json with your own bucket names, folder paths, and API keys:
```sh
{
    "input_bucket_name": "voice-memo-inputs",
    "output_bucket_name": "voice-memo-outputs",
    "inbox_folder": "TranscriptionInbox/",
    "processed_folder": "ProcessedTransAudio/",
    "icloud_folder": "~/Library/Mobile Documents/com~apple~CloudDocs/ProcessedTransAudio",
    "local_watch_folder": "~/Library/Mobile Documents/com~apple~CloudDocs/TranscriptionInbox",
    "poll_interval": 30,
    "openai_api_key": "your-openai-api-key"
}
```

### **5️⃣ Set Up iCloud Sync**
Create a symlink from iCloud's TranscriptionInbox to your project:

```sh
ln -s ~/Library/Mobile\ Documents/com~apple~CloudDocs/TranscriptionInbox ~/voice-memo-pipeline/data/inbox
```

### **📝 Usage Guide**
After 1-5, Run pipeline
```sh
python transcribe-sentiment.py
```
The script watches your iCloud & GCS folders.
When a new voice memo appears, it uploads → processes → saves insights automatically.

#### **Test with a Sample File**
- Drop a voice memo (or a .m4a file) into your iCloud TranscriptionInbox folder.
- Watch it sync to Google Cloud & get processed.
- Check iCloud & GCS for results (ProcessedTransAudio).

### **🛠️ Debugging & Logs**
If files don’t upload, check:

```sh
gcloud storage ls gs://voice-memo-inputs
```
If processing fails, inspect logs:

```sh
tail -f transcribe-sentiment.log
```

### **🚀 Future Enhancements**
🔹 Add Speaker Diarization – Identify different speakers in a conversation.
🔹 Improve Sentiment Analysis – Use a fine-tuned BERT model for better accuracy.
🔹 Event-Based Processing – Replace polling with Cloud Pub/Sub triggers.
🔹 Mobile App Integration – Build a lightweight app UI for memo tracking.

### **👤 Author**
Built by [@jeimcg](https://github.com/jeimcg) 🛠️
Connect with me on [LinkedIn](https://www.linkedin.com/in/jares-mcgill-71676222a/) 🚀

### **📜 License**
This project is licensed under the MIT License.
