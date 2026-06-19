"""Initiates and returns models from Azure OpenAI Cloud."""
# pylint: disable=import-error
# pylint: disable=no-name-in-module

import os
from langchain_openai.chat_models import AzureChatOpenAI
from langchain_openai.embeddings import AzureOpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()


def get_azure_models():
    """
    Initiates and returns models from Azure OpenAI Cloud.
    Returns:
        AzureChatOpenAI, AzureOpenAIEmbeddings, string: LLM, EMBEDDINGS_MODEL, "Azure OpenAI"
    """
    llm = AzureChatOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        api_version=os.getenv("OPENAI_API_VERSION"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    )

    embeddings_model = AzureOpenAIEmbeddings(
        model="text-embedding-3-small",
        azure_deployment=os.getenv("EMBEDDING_DEPLOYMENT_NAME"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_version=os.getenv("EMBEDDING_API_VERSION"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        dimensions=512,
    )
    return llm, embeddings_model, "Azure OpenAI"
