from typing import List
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI

from langgraph.graph import START, StateGraph, MessagesState
from langgraph.prebuilt import tools_condition, ToolNode

def add(a: int, b: int) -> int:
    """Adds a and b.

    Args:
        a: first int
        b: second int
    """
    return a + b


def check_middle(array: List[int], left: int, right: int, target: int) -> dict:
    """
    Check the middle element of the current search range.
    
    Args:
        array: The sorted array to search
        left: Left boundary of search range
        right: Right boundary of search range
        target: The number we're looking for
        
    Returns:
        Dictionary with middle index, value, and comparison result
    """
    middle = (left + right) // 2
    middle_value = array[middle]
    
    if middle_value == target:
        return {
            "middle": middle,
            "middle_value": middle_value,
            "comparison": "equal",
            "found": True
        }
    elif middle_value < target:
        return {
            "middle": middle,
            "middle_value": middle_value,
            "comparison": "less",
            "found": False
        }
    else:
        return {
            "middle": middle,
            "middle_value": middle_value,
            "comparison": "greater",
            "found": False
        }

def final_result(found: bool, index: int = None, explanation: str = "") -> dict:
    """
    Create a final result for the binary search.
    
    Args:
        found: Whether the target was found
        index: The index where target was found (if found)
        explanation: Explanation of the result
        
    Returns:
        FinalResult object with the search outcome
    """
    return {
            "found": found,
            "index": index,
            "explanation": explanation,
        }

def execute_binary_search_action(action: str, array: List[int], left: int, right: int, target: int) -> dict:
    """
    Execute a binary search action.
    
    Args:
        action: The action to perform
        array: The sorted array
        left: Current left boundary
        right: Current right boundary
        target: The target number
        
    Returns:
        Result of the action
    """
    if action == "check_middle":
        return check_middle(array, left, right, target)
    elif action == "search_left":
        return {"action": "search_left", "new_left": left, "new_right": (left + right) // 2 - 1}
    elif action == "search_right":
        return {"action": "search_right", "new_left": (left + right) // 2 + 1, "new_right": right}
    elif action == "found":
        return {"action": "found", "index": (left + right) // 2}
    elif action == "not_found":
        return {"action": "not_found", "index": -1}
    else:
        return {"error": f"Unknown action: {action}"}


# def check_middle(array: List[int], left: int, right: int, target: int) -> int:
#     """
#     Check the middle element of the current search range.
    
#     Args:
#         array: The sorted array to search
#         left: Left boundary of search range
#         right: Right boundary of search range
#         target: The number we're looking for
    
#     Returns:
#         int: 1 if the middle element is equal to the target, 0 if it is not
#     """
#     middle = left + (right - left) // 2
#     middle_value = array[middle]

#     if middle_value == target:
#         return 1
#     elif array[middle] < target:
#         return 0
#     else:
#         return 0

    
#     return 1 if array[left + (right - left) // 2] == target else 0



tools = [check_middle, final_result, execute_binary_search_action]

# Define LLM with bound tools
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
load_dotenv()
llm = init_chat_model("google_genai:gemini-2.0-flash")
# llm = ChatOpenAI(model="gpt-4o")
llm_with_tools = llm.bind_tools(tools)

# System message
sys_msg = SystemMessage(content="You are a helpful binary search assistant.")

# Node
def assistant(state: MessagesState):
   return {"messages": [llm_with_tools.invoke([sys_msg] + state["messages"])]}

# Build graph
builder = StateGraph(MessagesState)
builder.add_node("assistant", assistant)
builder.add_node("tools", ToolNode(tools))
builder.add_edge(START, "assistant")
builder.add_conditional_edges(
    "assistant",
    # If the latest message (result) from assistant is a tool call -> tools_condition routes to tools
    # If the latest message (result) from assistant is a not a tool call -> tools_condition routes to END
    tools_condition,
)
builder.add_edge("tools", "assistant")

# Compile graph
graph = builder.compile()
