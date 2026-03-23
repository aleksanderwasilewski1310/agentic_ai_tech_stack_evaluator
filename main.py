from dotenv import load_dotenv
from typing import Annotated, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_openai.chat_models import AzureChatOpenAI
from langchain_openai.embeddings import AzureOpenAIEmbeddings
from modules.db import push_ai_data_to_db
from modules.vectorizer import process_ai_response
from pydantic import BaseModel, Field
from typing_extensions import TypedDict
import os

load_dotenv()

llm = AzureChatOpenAI(azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                      azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
                      api_version=os.getenv("OPENAI_API_VERSION"),
                      api_key=os.getenv("AZURE_OPENAI_API_KEY"))

embeddings_model = AzureOpenAIEmbeddings(model="text-embedding-3-small",
                                         azure_deployment=os.getenv("EMBEDDING_DEPLOYMENT_NAME"),
                                         azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                                         api_version=os.getenv("EMBEDDING_API_VERSION"),
                                         api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                                         dimensions=512
                                         )                      

class MessageClassifier(BaseModel):
    message_type: Literal["python", "r", "vba"] = Field(
        ..., description="Classify if the Tool should be prepared in Python, R or VBA.")


class State(TypedDict):
    messages: Annotated[list, add_messages]
    message_type: str | None
    vector: list | None


def classify_message(state: State):
    last_message = state["messages"][-1]
    classifier_llm = llm.with_structured_output(MessageClassifier)
    result = classifier_llm.invoke([
        {
            "role": "system",
            "content": """Based on the description provided and following pros for each languages classify if the Tool should be Prepared in:
            - 'vba': VBA is tightly integrated with Microsoft Office applications like Excel,""" +
            """ making it ideal for automating repetitive tasks and building quick macros within these environments.""" +
            """ It requires minimal setup and is accessible to users familiar with Excel but less experienced in programming. """ +
            """ However, it is less versatile and powerful for complex data analysis compared to Python and R.
            - 'r': R is specifically designed for statistical analysis and visualization, """ +
            """ providing a rich ecosystem of packages tailored for advanced statistical modeling and data science. """ +
            """ It excels in exploratory data analysis and producing publication-quality graphics, often preferred by statisticians and researchers over Python and VBA. """ +
            """ While less general-purpose than Python, R’s specialized tools make it powerful for in-depth statistical work..
            - 'python': Python offers a versatile, easy-to-learn syntax with extensive libraries for data analysis, machine learning, and automation, """ +
            """ making it suitable for a wide range of applications beyond just data tasks. It has strong community support and integrates well with other systems, """ +
            """ outperforming VBA in scalability and R in general-purpose programming. Python’s flexibility makes it a top choice for both beginners and advanced users.
            """
        },
        {"role": "user", "content": last_message.content}
    ])
    return {"message_type": result.message_type}


def router(state: State):
    message_type = state.get("message_type", "vba")
    if message_type == "r":
        return {"next": "r"}
    elif message_type == "python":
        return {"next": "python"}
    return {"next": "vba"}
    pass


def python_agent(state: State):
    last_message = state["messages"][-1]

    messages = [
        {"role": "system",
         "content": """You are a Python Developer. Prepare a quick python solution for declared problem. Put the code inside markdown."""
         },
        {
            "role": "user",
            "content": last_message.content
        }
    ]
    reply = llm.invoke(messages)
    return {"messages": [{"role": "assistant", "content": reply.content}]}


def r_agent(state: State):
    last_message = state["messages"][-1]

    messages = [
        {"role": "system",
         "content": """You are a R Developer. Prepare a quick R Script solution for declared problem. Put the code inside markdown."""
         },
        {
            "role": "user",
            "content": last_message.content
        }
    ]
    reply = llm.invoke(messages)
    return {"messages": [{"role": "assistant", "content": reply.content}]}


def vba_agent(state: State):
    last_message = state["messages"][-1]

    messages = [
        {"role": "system",
         "content": """You are a VBA Developer. Prepare a quick VBA Macro Solution for declared problem. Put the code inside markdown."""
         },
        {
            "role": "user",
            "content": last_message.content
        }
    ]
    reply = llm.invoke(messages)
    return {"messages": [{"role": "assistant", "content": reply.content}]}

def vectonize_code(state: State):
    last_message = state["messages"][-1].content
    vector_data = process_ai_response(last_message)
    if hasattr(vector_data, "numpy"):
        vector_data = vector_data.numpy().flatten().tolist()
    return {"vector": vector_data}

graph_builder = StateGraph(State)

graph_builder.add_node("classifier", classify_message)
graph_builder.add_node("python", python_agent)
graph_builder.add_node("r", r_agent)
graph_builder.add_node("vba", vba_agent)
graph_builder.add_node("router", router)
graph_builder.add_node("vectonizer", vectonize_code)

graph_builder.add_edge(START, "classifier")
graph_builder.add_edge("classifier", "router")
graph_builder.add_conditional_edges(
    "router",
    lambda state: state.get("next"),
    {"python": "python", "r": "r", "vba": "vba"}
)
graph_builder.add_edge("python", "vectonizer")
graph_builder.add_edge("r", "vectonizer")
graph_builder.add_edge("vba", "vectonizer")
graph_builder.add_edge("vectonizer", END)

graph = graph_builder.compile()


# MAIN CHAT LOOP
def run_chatbot():
    print("--- Agentic AI Tech Stack Evaluator ---")
    while True:
        user_input = input("Message (type exit to close): ")
        if user_input.lower() == "exit":
            print("Shutting down...")
            break

        # Start with a fresh state (clears message history for every query)
        initial_state = {"messages": [{"role": "user", "content": user_input}]}
        
        # Execute graph
        final_state = graph.invoke(initial_state)
        
        # Extract data for processing and storage
        if "messages" in final_state and len(final_state["messages"]) >= 2:
            user_query = final_state["messages"][0].content
            solution = final_state["messages"][1].content
            msg_type = final_state.get('message_type')
            tf_vector = final_state.get("vector")
            
            # Generate Azure Embedding for the user's prompt
            azure_embedding = embeddings_model.embed_query(user_query)
            
            print(f"\n--- STACK: {msg_type.upper()} ---\n{solution}\n")
            
            # Save all data to PostgreSQL Vault
            push_ai_data_to_db(user_query, msg_type, solution, azure_embedding, tf_vector)

# Print ASCII graph visualization on startup
print(graph.get_graph().draw_ascii())

if __name__ == "__main__":
    run_chatbot()
    