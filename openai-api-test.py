import openai

openai.api_key = ""

try:
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, can you respond to this test message?"}
        ]
    )
    print("API Test Successful! Response:")
    print(response["choices"][0]["message"]["content"])
except Exception as e:
    print(f"API Test Failed: {e}")
