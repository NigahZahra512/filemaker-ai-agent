# AI Assistant for FileMaker Data Queries

A simple AI-powered assistant that lets non-technical users ask natural language questions about payment data stored in FileMaker, and get plain English answers — without needing to know FileMaker layouts, portals, or SQL.

## What It Does

This script:
1. Accepts a natural language question from the user (e.g., "How many payments are still pending?")
2. Sends the question to Google's Gemini AI model
3. Gemini decides which data it needs and requests it through a defined "tool"
4. The script fetches the actual data from a FileMaker database via the FileMaker Data API
5. Gemini uses that real data to generate a plain English answer

## Requirements

- Python 3.10 or higher
- A FileMaker Server with Data API access enabled
- A Google Gemini API key (free, available at https://aistudio.google.com/apikey)

## Setup Instructions

### 1. Clone or download this project

### 2. Install the required libraries

```bash
pip install google-generativeai requests python-dotenv
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

### 4. Make sure your FileMaker database has a `Payments` layout

The layout should have the following fields:

| Field Name | Type |
|---|---|
| PaymentID | Number |
| CustomerName | Text |
| Amount | Number |
| PaymentDate | Date |
| Status | Text |

## How to Run

```bash
python ai_agent.py
```

The script will prompt:

```
Ask your question:
```

Type your question and press Enter.

## Example Questions

- `How many payments are still pending?`
- `Show me the latest 5 payments`
- `What is the total amount of all payments?`

## Project Structure

```
filemaker-ai-agent/
├── ai_agent.py       # Main script — connects Gemini and FileMaker
├── .env              # Stores credentials (not committed to GitHub)
├── .gitignore        # Tells Git to ignore the .env file
└── README.md         # This file
```

## How It Works (Tool Calling)

This project uses a technique called **tool calling**. Gemini does not connect to FileMaker directly. Instead:

1. The user asks a question
2. Gemini decides if it needs data, and if so, which tool to call (`get_payments` or `get_total_amount`)
3. The Python script runs the actual FileMaker API call
4. The retrieved data is sent back to Gemini
5. Gemini uses that real data to write a plain English answer

This keeps precise calculations (like totals) accurate, since they are computed in Python rather than estimated by the AI.

## Notes

- This project currently supports a single FileMaker table (`Payments`) with two tools: fetching all payment records and calculating the total payment amount.
- Built as part of a one-week training project at Idiosol, under the mentorship of Sohaib Ahmed.