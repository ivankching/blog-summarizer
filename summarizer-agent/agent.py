from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.genai import types
from google.adk.tools.tool_context import ToolContext
from pathlib import Path

retry_config=types.HttpRetryOptions(
    attempts=5,  # Maximum retry attempts
    exp_base=7,  # Delay multiplier
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504], # Retry on these HTTP errors
)

def read_md_file(tool_context: ToolContext, filepath: str) -> dict:
    """
    Reads the content of a specified text file.

    Args:
        tool_context: The ADK tool context.
        filename: The name of the file to read.

    Returns:
        A dictionary containing the file content.
    """
    file_path = Path(filepath)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return {"status": "success", "content": content}
    except FileNotFoundError:
        return {"status": "error", "message": f"File not found: {filepath}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

root_agent = LlmAgent(
    name="summarizer",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    instruction="Your primary function is to read files using the provided tool and summarize their content.",
    tools=[read_md_file]
)