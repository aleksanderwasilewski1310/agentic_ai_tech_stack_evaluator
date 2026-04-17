"""Core module for AI Agent infrastructure."""

# pylint: disable=import-error
# pylint: disable=no-name-in-module
import logging
import os
from typing import Annotated, Literal
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_openai.chat_models import AzureChatOpenAI
from langchain_openai.embeddings import AzureOpenAIEmbeddings
from langchain_core.messages import AIMessage
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from modules.db import push_ai_data_to_db, find_similar_query_and_distance
from modules.vectorizer import process_ai_response

# Logger configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
LOGGER = logging.getLogger("AI-Agent")

load_dotenv()

LLM = AzureChatOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    api_version=os.getenv("OPENAI_API_VERSION"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
)

EMBEDDINGS_MODEL = AzureOpenAIEmbeddings(
    model="text-embedding-3-small",
    azure_deployment=os.getenv("EMBEDDING_DEPLOYMENT_NAME"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version=os.getenv("EMBEDDING_API_VERSION"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    dimensions=512,
)

# pylint: disable=too-few-public-methods


class MessageClassifier(BaseModel):
    """
    Data schema for the LLM-based message classification.

    This model enforces a strict output structure on the classifier agent,
    ensuring it selects exactly one of the supported programming languages.
    It serves as the contract between the LLM and the graph's routing logic.

    Attributes:
        message_type (Literal["python", "r", "vba"]): The chosen technology stack,
            constrained to Python, R, or VBA to ensure downstream compatibility.
    """

    message_type: Literal["python", "r", "vba"] = Field(
        ..., description="Classify if the Tool should be prepared in Python, R or VBA."
    )


class State(TypedDict):
    """
    Represents the shared state of the AI agent workflow.

    This dictionary acts as the short-term memory of the graph, tracking
    conversation history, classification results, and semantic search metadata
    to guide routing and response generation.

    Attributes:
        messages (Annotated[list, add_messages]): Append-only list of conversation
            history including system, user, and assistant messages.
        message_type (str | None): The identified technology stack (e.g., 'python',
            'r', 'vba') used for routing.
        vector (list | None): Numerical embedding of the latest assistant response
            ready for database storage.
        cached_response (str | None): Direct answer retrieved from vector store
            for high-confidence (90%+) semantic matches.
        similar_context (str | None): Historical task data used as RAG context
            for partial (70-89%) semantic matches.
    """

    messages: Annotated[list, add_messages]
    message_type: str | None
    vector: list | None
    cached_response: str | None  # 90%+ matches
    similar_context: str | None  # 70-89% matches


@retry(
    stop=stop_after_attempt(3),  # Try max 3 times
    wait=wait_exponential(multiplier=1, min=2, max=10),  # Wait 2s, 4s, 8s...
    retry=retry_if_exception_type(Exception),
    before_sleep=lambda retry_state: LOGGER.warning(
        "LLM Call failed. Retrying... (Attempt %s)", retry_state.attempt_number
    ),
)
def safe_llm_call(func, *args, **kwargs):
    """Generic wrapper to run any LLM-related call with retry logic."""
    return func(*args, **kwargs)


def get_tokens(reply: AIMessage, classifier_type: str):
    """Display Token used

    Args:
        reply (AIMessage): Reply from LLM
        classifier_type (str): classifier or vba/r/python agent
    """
    tokens_used = 0
    if hasattr(reply, "usage_metadata"):
        if reply.usage_metadata:
            usage = reply.usage_metadata
            tokens_used = usage["total_tokens"]
            LOGGER.info("Tokens used by %s: %d", classifier_type, tokens_used)
    return tokens_used


def check_cache_and_context(state: State):
    """
    Advanced semantic lookup node.
    - Distance < 0.1 (90% similarity): Triggers direct Cache Hit.
    - Distance 0.1 - 0.3 (70-90% similarity): Injects found solution as context for the LLM.
    """
    user_query = state["messages"][-1].content
    LOGGER.info("Checking semantic cache for query: %s", user_query[:50] + "...")
    query_embedding = EMBEDDINGS_MODEL.embed_query(user_query)

    # We need a modified DB function that returns both solution and distance
    solution, distance = find_similar_query_and_distance(query_embedding)

    if solution:
        LOGGER.info("Found similar query with distance: %.4f", distance)
        if distance < 0.1:
            LOGGER.info("Cache HIT (High confidence)")
            return {"cached_response": solution, "similar_context": None}
        if distance < 0.3:
            LOGGER.info("Partial semantic match - providing context")
            return {"cached_response": None, "similar_context": solution}

    LOGGER.info("Cache MISS")
    return {"cached_response": None, "similar_context": None}


def classify_message(state: State):
    """
    Classifies the user request to determine the optimal programming language for the task.

    Analyzes the latest message and optional RAG context to select between
    VBA, R, or Python based on specific strengths:
    - VBA: Excel automation and macros.
    - R: Statistical analysis and visualization.
    - Python: General-purpose programming and machine learning.

    Args:
        state (State): The current graph state containing conversation history
                       and optional semantic context from previous tasks.

    Returns:
        dict: A dictionary update containing the identified 'message_type'.
    """
    last_message = state["messages"][-1]
    context = state.get("similar_context")

    system_prompt = """Based on the description provided and following pros for each languages
                       classify if the Tool should be Prepared in:
                    - 'vba': VBA is tightly integrated with Microsoft Office applications like Excel,
                     making it ideal for automating repetitive tasks and building quick macros within these environments.
                     It requires minimal setup and is accessible to users familiar with Excel but less experienced in programming.
                     However, it is less versatile and powerful for complex data analysis compared to Python and R.
                    - 'r': R is specifically designed for statistical analysis and visualization,
                     providing a rich ecosystem of packages tailored for advanced statistical modeling and data science.
                     It excels in exploratory data analysis and producing publication-quality graphics,
                       often preferred by statisticians and researchers over Python and VBA.
                     While less general-purpose than Python, R’s specialized tools make it powerful for in-depth statistical work..
                    - 'python': Python offers a versatile, easy-to-learn syntax with extensive libraries for data analysis,
                     machine learning, and automation, making it suitable for a wide range of applications beyond just data tasks.
                     It has strong community support and integrates well with other systems,
                     outperforming VBA in scalability and R in general-purpose programming.
                       Python’s flexibility makes it a top choice
                         for both beginners and advanced users."""

    if context:
        print(f"\n⚪ Context added {context}.\n")
        system_prompt += f"\n\nCONTEXT FROM SIMILAR PREVIOUS TASK:\n{context}\n"
        system_prompt += (
            "Use the above context to ensure consistency in technology choice."
        )

    classifier_llm = LLM.with_structured_output(MessageClassifier)
    result = safe_llm_call(
        classifier_llm.invoke,
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": last_message.content},
        ],
    )
    get_tokens(result, "classifier")
    LOGGER.info("Classifier result: %s", result.message_type)
    return {"message_type": result.message_type}


def cache_router(state: State):
    """
    Directs the workflow based on the presence of a cached response.

    This router implements a cost-optimization step. If a semantically
    similar task was found in the vector database (cache), it bypasses
    further LLM processing. Otherwise, it triggers the classification flow.

    Args:
        state (State): The current graph state containing conversation
                       history and potential 'cached_response' from RAG.

    Returns:
        str: Next node to visit: "end_with_cache" if hit,
             "continue_to_classify" if miss.
    """
    if state.get("cached_response"):
        return "end_with_cache"
    return "continue_to_classify"


def router(state: State):
    """
    Determines the next execution node based on the classified message type.

    Acts as a conditional gateway in the graph, routing the workflow to
    specific language-based processing nodes (R, Python, or VBA).
    Defaults to 'vba' if the message type is unrecognized or missing.

    Args:
        state (State): The current graph state containing the 'message_type'
                       determined by the classifier node.

    Returns:
        dict: A dictionary with the "next" key specifying the destination node.
    """
    message_type = state.get("message_type", "vba")
    LOGGER.info("Routing to specialized agent: %s", message_type)
    if message_type == "r":
        return {"next": "r"}
    if message_type == "python":
        return {"next": "python"}
    return {"next": "vba"}


def python_agent(state: State):
    """
    Acts as a specialized Python Developer agent to solve technical problems.

    This node triggers a dedicated LLM chain with a system persona focused
    exclusively on Python engineering. It processes the user request
    and returns a solution formatted in Markdown, while tracking
    token consumption for the Python-specific task.

    Args:
        state (State): The current graph state containing the user's
                       problem description in the last message.

    Returns:
        dict: An update to the state messages with the assistant's Python
              solution and associated token usage metadata.
    """
    LOGGER.info("Starting Python agent processing")
    last_message = state["messages"][-1]

    messages = [
        {
            "role": "system",
            "content": """You are a Python Developer.
                           Prepare a quick python solution for declared problem.
                           Put the code inside markdown.""",
        },
        {"role": "user", "content": last_message.content},
    ]
    reply = safe_llm_call(LLM.invoke, messages)
    tokens_used = get_tokens(reply, "python agent")
    return {
        "messages": [
            {"role": "assistant", "content": reply.content, "tokens_usage": tokens_used}
        ]
    }


def r_agent(state: State):
    """
    Acts as a specialized R Developer agent to solve technical problems.

    This node triggers a dedicated LLM chain with a system persona focused
    exclusively on R engineering. It processes the user request
    and returns a solution formatted in Markdown, while tracking
    token consumption for the R-specific task.

    Args:
        state (State): The current graph state containing the user's
                       problem description in the last message.

    Returns:
        dict: An update to the state messages with the assistant's R
              solution and associated token usage metadata.
    """
    LOGGER.info("Starting R agent processing")
    last_message = state["messages"][-1]

    messages = [
        {
            "role": "system",
            "content": """You are a R Developer.
                          Prepare a quick R Script solution for declared problem.
                          Put the code inside markdown.""",
        },
        {"role": "user", "content": last_message.content},
    ]
    reply = safe_llm_call(LLM.invoke, messages)
    tokens_used = get_tokens(reply, "r agent")
    return {
        "messages": [
            {"role": "assistant", "content": reply.content, "tokens_usage": tokens_used}
        ]
    }


def vba_agent(state: State):
    """
    Acts as a specialized VBA Developer agent to solve technical problems.

    This node triggers a dedicated LLM chain with a system persona focused
    exclusively on VBA programming. It processes the user request
    and returns a solution formatted in Markdown, while tracking
    token consumption for the VBA-specific task.

    Args:
        state (State): The current graph state containing the user's
                       problem description in the last message.

    Returns:
        dict: An update to the state messages with the assistant's VBA
              solution and associated token usage metadata.
    """
    LOGGER.info("Starting VBA agent processing")
    last_message = state["messages"][-1]

    messages = [
        {
            "role": "system",
            "content": """You are a VBA Developer.
                          Prepare a quick VBA Macro Solution for declared problem.
                          Put the code inside markdown.""",
        },
        {"role": "user", "content": last_message.content},
    ]
    reply = safe_llm_call(LLM.invoke, messages)
    tokens_used = get_tokens(reply, "vba agent")
    return {
        "messages": [
            {"role": "assistant", "content": reply.content, "tokens_usage": tokens_used}
        ]
    }


def vectonize_code(state: State):
    """
    Transforms the assistant's generated code into a numerical vector representation.

    This node triggers the embedding pipeline to convert textual responses
    into semantic vectors. It handles tensor-to-list conversion to ensure
    compatibility with the PostgreSQL/pgvector storage layer.

    Args:
        state (State): The current graph state containing the last assistant
                       message to be vectorized.

    Returns:
        dict: A dictionary update containing the 'vector' field with the
              flattened numerical embedding.
    """
    LOGGER.info("Vectorizing AI response for long-term vault")
    last_message = state["messages"][-1].content
    vector_data = process_ai_response(last_message)
    numpy_method = getattr(vector_data, "numpy", None)
    if numpy_method:
        # pylint: disable=no-member
        vector_data = vector_data.numpy().flatten().tolist()
    return {"vector": vector_data}


GRAPH_BUILDER = StateGraph(State)

GRAPH_BUILDER.add_node("check_cache", check_cache_and_context)
GRAPH_BUILDER.add_node("classifier", classify_message)
GRAPH_BUILDER.add_node("python", python_agent)
GRAPH_BUILDER.add_node("r", r_agent)
GRAPH_BUILDER.add_node("vba", vba_agent)
GRAPH_BUILDER.add_node("router", router)
GRAPH_BUILDER.add_node("vectonizer", vectonize_code)

GRAPH_BUILDER.add_edge(START, "check_cache")
GRAPH_BUILDER.add_edge("classifier", "router")

GRAPH_BUILDER.add_conditional_edges(
    "check_cache",
    cache_router,
    {"end_with_cache": END, "continue_to_classify": "classifier"},
)

GRAPH_BUILDER.add_conditional_edges(
    "router",
    lambda state: state.get("next"),
    {"python": "python", "r": "r", "vba": "vba"},
)
GRAPH_BUILDER.add_edge("python", "vectonizer")
GRAPH_BUILDER.add_edge("r", "vectonizer")
GRAPH_BUILDER.add_edge("vba", "vectonizer")
GRAPH_BUILDER.add_edge("vectonizer", END)

GRAPH = GRAPH_BUILDER.compile()


# MAIN CHAT LOOP
def run_chatbot():
    """
    Runs the main chatbot
    """
    LOGGER.info("--- Agentic AI Tech Stack Evaluator Started ---")
    while True:
        user_input = input("Message (type exit to close): ")  # nosec
        if user_input.lower() == "exit":
            print("Shutting down...")
            break

        # Start with a fresh state (clears message history for every query)
        initial_state = {"messages": [{"role": "user", "content": user_input}]}

        # Execute graph
        final_state = GRAPH.invoke(initial_state)

        # Extract data for processing and storage
        if "messages" in final_state and len(final_state["messages"]) >= 2:
            user_query = final_state["messages"][0].content
            solution = final_state["messages"][1].content
            last_msg = final_state["messages"][-1]
            tokens_used = last_msg.additional_kwargs.get("tokens_usage", 0)
            msg_type = final_state.get("message_type")
            tf_vector = final_state.get("vector")

            # Generate Azure Embedding for the user's prompt
            azure_embedding = EMBEDDINGS_MODEL.embed_query(user_query)

            print(f"\n--- STACK: {msg_type.upper()} ---\n{solution}\n")

            # Save all data to PostgreSQL Vault
            ai_data = {
                "query": user_query,
                "stack": msg_type,
                "code": solution,
                "azure_vec": azure_embedding,
                "tf_model_output": tf_vector,
                "tokens_used": tokens_used,
            }
            push_ai_data_to_db(ai_data)

        # If there is a cached response
        else:
            solution = final_state["cached_response"]
            print(f"\n---CACHED SOLUTION---\n{solution}\n")


# Print ASCII graph visualization on startup
print(GRAPH.get_graph().draw_ascii())

if __name__ == "__main__":
    run_chatbot()
