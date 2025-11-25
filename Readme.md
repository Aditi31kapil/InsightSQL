🌍 InsightSQL Analyst

📖 Overview

The InsightSQL Analyst is an advanced data analysis tool designed to bridge the gap between non-technical users and complex database systems. By leveraging Generative AI, this application allows users to interact with SQLite databases using natural language—whether through text or voice commands—in their native language.

The system automatically translates queries, generates the appropriate SQL, executes it against the database, and presents the results as interactive visualizations and data summaries.

✨ Key Features

🗣️ Voice-Activated Querying: Use your microphone to ask questions hands-free.

🌐 Multilingual Support: Ask questions in Hindi, Spanish, French, or any other language supported by Deep Translate.

🤖 Automated SQL Generation: Converts natural language questions into complex SQL queries using LLMs.

📊 Dynamic Visualization: Automatically detects data types and generates interactive Plotly charts (Bar, Line, Scatter, etc.).

📂 Dataset Agnostic: Upload any .sqlite or .db file and instantly start analyzing.

🔍 Database Inspector: Preview tables and schema immediately after upload.

🛠️ Tech Stack

Frontend: Streamlit

Data Processing: Pandas, SQLite3

AI & NLP:

deep_translator for language translation.

SpeechRecognition for voice input.

LLM Integration (e.g., Gemini/OpenAI) for SQL generation and summarization.

Visualization: Plotly Express

🚀 Installation & Setup

Clone the Repository

git clone [https://github.com/Aditi31kapil/InsightSQL](https://github.com/Aditi31kapil/InsightSQL)
cd multilingual-sql-analyst

Create a Virtual Environment

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate


Install Dependencies

pip install -r requirements.txt


Note: For voice recognition, you may need to install pyaudio. On Windows, pip install pyaudio works directly. On Linux, you may need sudo apt-get install python3-pyaudio.

Set up API Keys

Create a .env file or set up your environment variables for your LLM provider (e.g., Llama_api_key).

Run the Application

streamlit run app.py


📂 Project Structure

├── app.py                # Main Streamlit application
├── db_utils.py           # Database connection and schema extraction logic
├── llm_api.py            # LLM interaction (SQL generation, Plot code)
├── requirements.txt      # Project dependencies
├── uploaded_db.sqlite    # Temporary storage for uploaded DB (gitignored)
└── README.md             # Project documentation


🎯 Usage Guide

Upload Data: Use the sidebar to upload your .sqlite database file.

Select Input: Choose between "Text Input" or "Voice".

Ask a Question:

Example: "Show me the top 5 customers by total purchase."

Example (Hindi): "Sabse zyada sales wale 3 products dikhao."

View Results: The app will display:

The generated SQL query.

The raw data table.

An interactive chart (if applicable).

A text summary of the findings.

🤝 Contributing

Contributions are welcome! Please fork the repository and submit a Pull Request.

📄 License

This project is licensed under the MIT License.