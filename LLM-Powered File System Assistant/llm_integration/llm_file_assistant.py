import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("OPENAI_MODEL", "openai/gpt-oss-20b")

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

BASE_DIRECTORY = os.path.join(os.getcwd(), "data")

from fsTolls.fsTolls import (
    read_file,
    list_files,
    write_file,
    search_in_file
)

TOOLS = {
    "read_file": read_file,
    "list_files": list_files,
    "write_file": write_file,
    "search_in_file": search_in_file,
}

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read content of a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string"}
                },
                "required": ["filepath"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files in a directory",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string"},
                    "extension": {"type": "string"}
                },
                "required": ["directory"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_in_file",
            "description": "Search keyword inside a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string"},
                    "keyword": {"type": "string"}
                },
                "required": ["filepath", "keyword"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to file",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string"},
                    "content": {"type": "string"},
                    "mode": {"type": "string"}
                },
                "required": ["filepath", "content"]
            }
        }
    }
]


def ask_llm_with_tools(messages):
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=TOOLS_SCHEMA,
        tool_choice="auto"
    )
    return response


def execute_tool(tool_name, arguments):
    if tool_name not in TOOLS:
        return {"error": "Tool not found"}

    # 🔥 Force safe directory
    if "directory" in arguments:
        arguments["directory"] = BASE_DIRECTORY

    try:
        return TOOLS[tool_name](**arguments)
    except Exception as e:
        return {"error": str(e)}


def handle_query(user_query):
    messages = [
        {
            "role": "system",
            "content": f"""
You are an intelligent file assistant.

All files are inside: {BASE_DIRECTORY}

IMPORTANT:
- Most files are PDFs
- Default extension should be ".pdf"
- Do NOT explore outside this directory
- If no files found, do NOT try other directories

Rules:
- Always use tools for file operations
- Think step-by-step
"""
        },
        {"role": "user", "content": user_query}
    ]

    for _ in range(10):
        response = ask_llm_with_tools(messages)
        msg = response.choices[0].message

        if msg.tool_calls:
            # ✅ Correct assistant message format
            messages.append({
                "role": "assistant",
                "tool_calls": msg.tool_calls
            })

            for tool_call in msg.tool_calls:
                tool_name = tool_call.function.name

                # ✅ Safe JSON parsing
                try:
                    args = json.loads(tool_call.function.arguments)
                except Exception:
                    print("Bad arguments:", tool_call.function.arguments)
                    continue

                print("TOOL CALL:", tool_name, args)

                result = execute_tool(tool_name, args)

                print("TOOL RESULT:", result)

                # ✅ Handle empty results
                if isinstance(result, list) and len(result) == 0:
                    messages.append({
                        "role": "system",
                        "content": "No files found in the directory. Do not try other directories."
                    })

                # ✅ Send tool result back
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result)
                })

        else:
            print("FINAL RESPONSE:", msg.content)
            return msg.content

    return "Error: Too many tool calls"