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
    """Logs in to FileMaker and returns a session token."""
    login_url = f"https://{FILEMAKER_HOST}/fmi/data/vLatest/databases/{FILEMAKER_DATABASE}/sessions"
    response = requests.post(
        login_url,
        auth=(FILEMAKER_USERNAME, FILEMAKER_PASSWORD),
        json={},
        verify=False
    )
    return response.json()["response"]["token"]


# ---------- NEW FUNCTION ----------
# This is the new piece. Instead of knowing table names in advance,
# this function asks FileMaker directly: "what layouts/tables do you have?"
# FileMaker has a built-in endpoint just for this purpose.
def list_available_layouts():
    """
    Asks FileMaker for the list of all layout names in the database.
    This means we don't need to hardcode table names anymore - 
    whatever layout Zeeshan creates, this will automatically detect it.
    """
    token = get_filemaker_token()
    url = f"https://{FILEMAKER_HOST}/fmi/data/vLatest/databases/{FILEMAKER_DATABASE}/layouts"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers, verify=False)
    data = response.json()["response"]["layouts"]

    # FileMaker returns layout names (and sometimes folders/groups).
    # We only want the plain layout names, so we filter for items that
    # have a "name" key (folders show up differently in the response).
    layout_names = [item["name"] for item in data if "name" in item]
    return layout_names


# ---------- UPDATED FUNCTION (was get_payments) ----------
# Before: this only worked for the "Payments" layout (hardcoded).
# Now: it accepts ANY layout name as a parameter, so it works for
# whatever table Zeeshan creates - Customers, Orders, anything.
def get_records(layout_name):
    """Fetches all records from ANY given FileMaker layout (table)."""
    token = get_filemaker_token()
    url = f"https://{FILEMAKER_HOST}/fmi/data/vLatest/databases/{FILEMAKER_DATABASE}/layouts/{layout_name}/records"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers, verify=False)
    data = response.json()["response"]["data"]

    records = []
    for record in data:
        records.append(record["fieldData"])
    return records


def get_total_amount(layout_name, field_name="Amount"):
    """
    Calculates the total of a numeric field for any layout, using Python
    (not AI), so the math is always exact.
    """
    records = get_records(layout_name)
    total = sum(float(r[field_name]) for r in records if field_name in r)
    return total


# ---------- Gemini Setup ----------

genai.configure(api_key=GEMINI_API_KEY)

# ---------- UPDATED TOOL DEFINITIONS ----------
# Notice the "parameters" sections are no longer empty - now Gemini
# must tell us WHICH layout it wants, because we no longer assume
# "Payments" by default.

list_layouts_tool = {
    "name": "list_available_layouts",
    "description": (
        "Returns the list of all available tables/layouts in the FileMaker "
        "database. Use this FIRST whenever you are not sure which table "
        "contains the data needed to answer the user's question, or when "
        "the user asks what data/tables are available."
    ),
    "parameters": {
        "type": "object",
        "properties": {}
    }
}

get_records_tool = {
    "name": "get_records",
    "description": (
        "Fetches ALL records from a specific FileMaker table/layout. "
        "Use this for any question about the contents of a specific table "
        "(filtering, sorting, counting, finding specific records, etc). "
        "You must specify which layout_name to fetch from. If you don't "
        "know the available layout names yet, call list_available_layouts first."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "layout_name": {
                "type": "string",
                "description": "The exact name of the FileMaker layout/table to fetch records from."
            }
        },
        "required": ["layout_name"]
    }
}

get_total_amount_tool = {
    "name": "get_total_amount",
    "description": (
        "Calculates the exact sum of a numeric field (like Amount) across "
        "all records in a given layout/table, using precise calculation. "
        "Use this when the user asks for a total/sum."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "layout_name": {
                "type": "string",
                "description": "The exact name of the FileMaker layout/table."
            },
            "field_name": {
                "type": "string",
                "description": "The name of the numeric field to sum (defaults to 'Amount' if not specified)."
            }
        },
        "required": ["layout_name"]
    }
}

model = genai.GenerativeModel(
    "gemini-2.5-flash",
    tools=[{"function_declarations": [list_layouts_tool, get_records_tool, get_total_amount_tool]}]
)

# ---------- Helper: actually run whichever tool Gemini asked for ----------

def call_tool(tool_name, args):
    """
    Looks at the tool name Gemini requested, and the arguments Gemini gave,
    and calls the matching Python function with those arguments.
    """
    if tool_name == "list_available_layouts":
        return list_available_layouts()
    elif tool_name == "get_records":
        return get_records(args.get("layout_name"))
    elif tool_name == "get_total_amount":
        return get_total_amount(args.get("layout_name"), args.get("field_name", "Amount"))
    else:
        return {"error": f"Unknown tool: {tool_name}"}


# ---------- Main Logic ----------
# This now supports MULTIPLE rounds of tool calls, because answering a
# question might need two steps: first "what layouts exist?", then
# "get records from that specific layout".

def ask(user_question, max_turns=5):
    conversation = [{"role": "user", "parts": [{"text": user_question}]}]

    for _ in range(max_turns):
        response = model.generate_content(conversation)
        part = response.candidates[0].content.parts[0]

        if hasattr(part, "function_call") and part.function_call.name:
            tool_name = part.function_call.name
            args = dict(part.function_call.args) if part.function_call.args else {}
            print(f"Calling tool: {tool_name}({args})...")

            result_data = call_tool(tool_name, args)

            # Add Gemini's request and our result to the conversation,
            # then loop again - Gemini might need to call another tool,
            # or might be ready to give the final answer.
            conversation.append({"role": "model", "parts": [{"function_call": part.function_call}]})
            conversation.append({
                "role": "user",
                "parts": [{"function_response": {
                    "name": tool_name,
                    "response": {"result": result_data}
                }}]
            })
        else:
            return response.text

    return "Sorry, I couldn't get a final answer within the allowed steps."


if __name__ == "__main__":
    user_question = input("Ask your question: ")
    answer = ask(user_question)
    print("\nFinal Answer:")
    print(answer)