# Generative_AI

 Team Project of Generative AI SP II 2025
 
# Financial PDF Analyzer (Powered by OpenAI Assistants API)

This project is a local GUI application that lets you upload PDF financial reports, analyze them using OpenAI's Assistants API, and receive structured insights (tables, summaries) as responses. You can also chat with the same assistant.

# 📌 1. Register OpenAI API

To use this tool, you’ll need an OpenAI API key:

Go to https://platform.openai.com/account/api-keys

Sign in with your OpenAI account (or register one for free)

Click "Create new secret key" and copy it (you'll use this in the app)

# 🤖 2. Create an Assistant on OpenAI

You also need an Assistant in your OpenAI account. Here's how:

Visit the Assistants page: https://platform.openai.com/assistants

Click "Create Assistant"

Recommended Settings:

Model: gpt-4o-mini (affordable & supports file analysis) or gpt-4-turbo

Tools: Enable ✅ File Search

Code Interpreter: ❌ Disable

Functions: leave empty

Response format: text

Temperature: 0

Click "Save"

Copy the Assistant ID (looks like asst_abc123...)

# 3. Install Dependencies

Make sure Python 3.9+ is installed. Then install dependencies via:

pip install -r requirements.txt

# 4. Run the Application

python main.py

# 🔐 5. Configure API Key and Assistant ID

Before using the app, click Settings and input the following:

API Key: Paste the key you got from step 1

Assistant ID: Paste the asst_... ID you got from step 2

Download Directory: Optional—choose where downloaded PDFs are stored

Click Confirm to save. You’re ready to go!
