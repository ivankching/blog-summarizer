from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.genai import types
from google.adk.tools.tool_context import ToolContext
from google.adk.sessions import DatabaseSessionService
from pathlib import Path

from blog_agent.substack import download_substack_posts
from blog_agent.html_reader import batch_convert

db_url = "sqlite:///blog_agent_data.db"
session_service = DatabaseSessionService(db_url=db_url)

retry_config=types.HttpRetryOptions(
    attempts=5,  # Maximum retry attempts
    exp_base=7,  # Delay multiplier
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504], # Retry on these HTTP errors
)

def update_username(tool_context: ToolContext, username: str):
    """
    Updates the username stored in the tool context state.

    Args:
        tool_context (ToolContext): The ToolContext object containing the state of the conversation
        username (str): The username to update

    Returns:
        Dictionary containing the status of the update and a message describing the result.
        Success: {"status": "success", "message": "Username updated successfully"}
        Error: {"status": "error", "message": "Error updating username"}
    """
    try:
        tool_context.state["username"] = username
        return {"status": "success", "message": "Username updated successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
def update_date(tool_context: ToolContext, date_str: str):
    """
    Updates the date stored in the tool context state.

    Args:
        tool_context (ToolContext): The ToolContext object containing the state of the conversation
        date_str (str): The date to update in the format %Y-%m-%dT%H:%M:%S.%f%z

    Returns:
        Dictionary containing the status of the update and a message describing the result.
        Success: {"status": "success", "message": "Date updated successfully"}
        Error: {"status": "error", "message": "Error updating date"}
    """
    try:
        tool_context.state["date"] = date_str
        return {"status": "success", "message": "Date updated successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
def get_username(tool_context: ToolContext):
    """
    Retrieves the username stored in the tool context state.

    Args:
        tool_context (ToolContext): The ToolContext object containing the state of the conversation

    Returns:
        str: The username stored in the tool context state
    """
    return tool_context.state.get("username", None)

def get_date(tool_context: ToolContext):
    """
    Retrieves the date stored in the tool context state.

    Args:
        tool_context (ToolContext): The ToolContext object containing the state of the conversation

    Returns:
        str: The date stored in the tool context state
    """
    return tool_context.state.get("date", None)

def get_posts(username: str, date_str: str):
    response = download_substack_posts(username, date_str)
    """
    Downloads posts from substack for a given username and date.

    Args:
        username (str): The username to download posts for
        date_str (str): The date to download posts from in the format %Y-%m-%dT%H:%M:%S.%f%z

    Returns:
        Dictionary containing the status of the download and a message describing the result.
        Success: {"status": "success", "message": "Posts downloaded successfully"}
        Error: {"status": "error", "message": "Error downloading posts"}
    """

    if response["status"] == "error":
        return {"status": "error", "message": "Error downloading posts"}
    
    return batch_convert("post_content")


root_agent = LlmAgent(
    name="blog_manager",
    model=Gemini(
        model="gemini-2.5-flash-lite",
        retry_options=retry_config
    ),
    instruction="""Your primary function is to get posts from substack using the get_posts tool. Say 'download completed' when you are done.
    If the username is not provided, use the get_username tool to get the username. If the result is None, ask the user to provide a username.
    If the date is not provided, use the get_date tool to get the date. If the result is None, ask the user to provide a date.
    Whenever the user provides a username, use the update_username tool to update the username in the tool context state.
    Whenever the user provides a date, use the update_date tool to update the date in the tool context state.""",
    tools=[get_posts, update_username, update_date, get_username, get_date],
)