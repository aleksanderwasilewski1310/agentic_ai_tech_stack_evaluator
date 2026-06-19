"""
Dynamically loads the LLM and Embeddings based on the environment variable.
Defaults to Azure if no provider is explicitly defined.
"""

# pylint: disable=import-error
import os
from dotenv import load_dotenv
from .azure_openai import get_azure_models
from .aws_bedrock import get_bedrock_models

load_dotenv()


def load_agent_models():
    """
    Dynamically loads the LLM and Embeddings based on the environment variable.
    """
    provider = os.getenv("MODEL_PROVIDER", "azure").lower()

    if provider == "aws":
        return get_bedrock_models()

    if provider == "azure":
        return get_azure_models()

    return get_azure_models()
