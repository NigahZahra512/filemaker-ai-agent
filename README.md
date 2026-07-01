# AI Assistant for FileMaker Data Queries

A simple AI-powered assistant that lets non-technical users ask natural language questions about data stored in FileMaker, and get plain English answers — without needing to know FileMaker layouts, portals, or SQL.

## What It Does

This project:
1. Accepts a natural language question from the user (e.g., "How many payments are still pending?")
2. Sends the question to Google's Gemini AI model
3. Gemini decides which table it needs data from, and requests it through a defined "tool"
4. The script fetches the actual data from a FileMaker database via the FileMaker Data API
5. Gemini uses that real data to generate a plain English answer

The assistant is not limited to a single table — it can automatically detect and query **any table (layout)** available in the connected FileMaker database.

## Two Ways to Use It

1. **Terminal version** (`ai_agent.py`) — ask a question directly in the command line
2. **Streamlit UI version** (`app.py`) — a simple chat-style web interface with a sidebar showing available tables and chat history

## Requirements

- Python 3.10 or higher
- A FileMaker Server with Data API access enabled
- A Google Gemini API key (free, available at https://aistudio.google.com/apikey)

## Setup Instructions

### 1. Clone or download this project

### 2. Install the required libraries

```bash
pip install google-generativeai requests python-dotenv streamlit
```

### 3. Create a `.env` file

In the project folder, create a file named `.env` (no file extension) and add the following, replacing the placeholder values with your actual credentials:

```
FILEMAKER_HOST=your_filemaker_host
FILEMAKER_DATABASE=your_database_name
FILEMAKER_USERNAME=your_filemaker_username
FILEMAKER_PASSWORD=your_filemaker_password
GEMINI_API_KEY=your_gemini_api_key
```

**Important:** Never commit the `.env` file to GitHub. It is already excluded via `.gitignore`.

### 4. No table setup required

Unlike earlier versions, this assistant does not require a specific table name to be known in advance. It automatically detects all available layouts (tables) in the connected FileMaker database.

## How to Run

**Terminal version:**
```bash
python ai_agent.py
```
The script will prompt:
```
Ask your question:
```
Type your question and press Enter.

**Streamlit UI version:**
```bash
streamlit run app.py
```
This will open a chat interface in your browser, with a sidebar listing all available tables.

## Example Questions

- `What tables are available?`
- `How many records are in the Payments table?`
- `What is the total amount of all payments?`
- `Show me all records in the Customers table`

## Project Structure

```
filemaker-ai-agent/
├── ai_agent.py       # Main script — connects Gemini and FileMaker, defines all tools
├── app.py            # Streamlit chat interface
├── .env              # Stores credentials (not committed to GitHub)
├── .gitignore        # Tells Git to ignore .env and __pycache__
└── README.md         # This file
```

## How It Works (Tool Calling)

This project uses a technique called **tool calling**. Gemini does not connect to FileMaker directly. Instead:

1. The user asks a question
2. Gemini decides if it needs data, and which tool to call:
   - `list_available_layouts` — to see what tables exist
   - `get_records` — to fetch all records from a specific table
   - `get_total_amount` — to calculate an exact total of a numeric field
3. The Python script runs the actual FileMaker API call
4. The retrieved data is sent back to Gemini
5. Gemini uses that real data to write a plain English answer, looping through multiple tool calls if needed (up to 5 steps per question)

This keeps precise calculations (like totals) accurate, since they are computed in Python rather than estimated by the AI.

## Notes

- This project now supports **any table/layout** in the connected FileMaker database, not just a single hardcoded one.
- Built as part of a training project at Idiosol, under the mentorship of Sohaib Ahmed.
- This version uses the `google-generativeai` Python package, which Google has marked for deprecation in favor of `google-genai`. A future update may migrate to the new package.