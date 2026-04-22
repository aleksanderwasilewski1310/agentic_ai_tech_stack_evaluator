"""
AI Agent Infrastructure with FastAPI & Chainlit Integration.
Focus: Multi-agent routing, semantic caching, and asynchronous interface.
"""

import asyncio
import chainlit as cl
from fastapi import FastAPI
from pydantic import BaseModel
from main import GRAPH, EMBEDDINGS_MODEL, push_ai_data_to_db

# --- [FASTAPI INITIALIZATION] ---
# Creating an API entry point for external microservices integration
APP = FastAPI(title="AI Stack Evaluator API")


class ChatRequest(BaseModel):
    """
    Chat Request Class
    """

    query: str


# --- [CHAINLIT INTEGRATION - ASYNC UI] ---
# Using Chainlit to provide a production-grade chat interface


@cl.on_chat_start
async def on_chat_start():
    """
    Initializes the session-based state.
    Store the compiled graph in the user session for persistence.
    """
    cl.user_session.set("graph", GRAPH)
    await cl.Message(
        content="AI Tech Stack Evaluator is online. How can I assist your engineering workflow?"
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    """
    Main entry point for Chainlit UI.
    Handles async execution of the LangGraph workflow.
    """
    graph = cl.user_session.get("graph")

    # Initialize state with the user's message
    # Consistent with the Graph's State TypedDict
    initial_state = {"messages": [{"role": "user", "content": message.content}]}

    # Executing the graph asynchronously to prevent UI blocking
    final_state = await graph.ainvoke(initial_state)

    # Logical branch: Handle Cache Hit vs Model Generation
    if final_state.get("cached_response"):
        response = f"**[SEMANTIC CACHE HIT]**\n\n{final_state['cached_response']}"
    else:
        # 1. Extract data from final_state
        user_query = message.content
        solution = final_state["messages"][-1].content
        stack = final_state.get("message_type", "N/A")

        # Get tokens from metadata (consistent with your get_tokens function)
        last_msg = final_state["messages"][-1]
        # In LangGraph/AIMessage tokens are often in response_metadata or additional_kwargs
        tokens_used = (
            getattr(last_msg, "response_metadata", {})
            .get("token_usage", {})
            .get("total_tokens", 0)
        )

        # 2. Prepare visual response
        response = f"**SELECTED STACK: {stack.upper()}**\n\n{solution}"

        # 3. PREPARE AI_DATA FOR DATABASE
        # We need to generate embedding for the new query to save it for future RAG/Cache hits
        query_vector = EMBEDDINGS_MODEL.embed_query(user_query)
        tf_vector = final_state.get("vector")  # From your vectonizer node

        ai_data = {
            "query": user_query,
            "stack": stack,
            "code": solution,
            "azure_vec": query_vector,
            "tf_model_output": tf_vector,
            "tokens_used": tokens_used,
        }

        # 4. ASYNC DATABASE PUSH
        # Using executor to not block the chat UI while DB is processing
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, push_ai_data_to_db, ai_data)

    await cl.Message(content=response).send()


# --- [FASTAPI ENDPOINT] ---
# Providing a RESTful interface for headless integration


@APP.post("/v1/predict")
async def predict(request: ChatRequest):
    """
    Production REST endpoint.
    Ideal for integration with CI/CD pipelines or external legacy systems.
    """
    initial_state = {"messages": [{"role": "user", "content": request.query}]}
    # Synchronous or Asynchronous invocation depending on deployment requirements
    result = await GRAPH.ainvoke(initial_state)

    return {
        "stack": result.get("message_type"),
        "cached": bool(result.get("cached_response")),
        "answer": result["messages"][-1].content
        if not result.get("cached_response")
        else result.get("cached_response"),
    }
