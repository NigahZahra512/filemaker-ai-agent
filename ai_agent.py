import os
from dotenv import load_dotenv
import google.generativeai as genai
import requests
import urllib3
import json

# Load environment variables from the .env file
load_dotenv()

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Read credentials from environment variables instead of hardcoding them
FILEMAKER_HOST = os.getenv("FILEMAKER_HOST")
FILEMAKER_DATABASE = os.getenv("FILEMAKER_DATABASE")
FILEMAKER_USERNAME = os.getenv("FILEMAKER_USERNAME")
FILEMAKER_PASSWORD = os.getenv("FILEMAKER_PASSWORD")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ---------- FileMaker Functions ----------

def get_filemaker_token():
    login_url = f"https://{FILEMAKER_HOST}/fmi/data/vLatest/databases/{FILEMAKER_DATABASE}/sessions"
    response = requests.post(
        login_url,
        auth=(FILEMAKER_USERNAME, FILEMAKER_PASSWORD),
        json={},
        verify=False
    )
    return response.json()["response"]["token"]


def get_payments():
    """Fetches all payment records from the FileMaker Payments layout."""
    token = get_filemaker_token()
    url = f"https://{FILEMAKER_HOST}/fmi/data/vLatest/databases/{FILEMAKER_DATABASE}/layouts/Payments/records"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers, verify=False)
    data = response.json()["response"]["data"]

    records = []
    for record in data:
        records.append(record["fieldData"])
    return records


def get_total_amount():
    """Calculates the total amount of all payments using Python (not AI)."""
    payments = get_payments()
    total = sum(float(p["Amount"]) for p in payments)
    return total


# ---------- Gemini Setup ----------

genai.configure(api_key=GEMINI_API_KEY)

get_payments_tool = {
    "name": "get_payments",
    "description": "Fetches ALL payment records from the FileMaker Payments table. Use this tool for ANY question about payments, including filtering, sorting, counting, or finding specific records like 'latest N payments', 'pending payments', etc. Each record has PaymentID, CustomerName, Amount, PaymentDate, and Status (Paid or Pending). After fetching, you can filter/sort/analyze the data yourself to answer the user's specific question.",
    "parameters": {
        "type": "object",
        "properties": {}
    }
}

get_total_amount_tool = {
    "name": "get_total_amount",
    "description": "Calculates and returns the exact total sum of all payment amounts using precise calculation.",
    "parameters": {
        "type": "object",
        "properties": {}
    }
}

model = genai.GenerativeModel(
    "gemini-2.5-flash",
    tools=[{"function_declarations": [get_payments_tool, get_total_amount_tool]}]
)

# ---------- Main Logic ----------

user_question = input("Ask your question: ")

response = model.generate_content(user_question)

part = response.candidates[0].content.parts[0]

if hasattr(part, "function_call") and part.function_call.name:
    tool_name = part.function_call.name
    print(f"Calling tool: {tool_name}...")

    if tool_name == "get_payments":
        result_data = get_payments()
    elif tool_name == "get_total_amount":
        result_data = get_total_amount()

    final_response = model.generate_content([
        {"role": "user", "parts": [{"text": user_question}]},
        {"role": "model", "parts": [{"function_call": part.function_call}]},
        {"role": "user", "parts": [{"function_response": {
            "name": tool_name,
            "response": {"result": result_data}
        }}]}
    ])

    print("\nFinal Answer:")
    print(final_response.text)
else:
    print(response.text)