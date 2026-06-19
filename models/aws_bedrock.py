"""Initiates and returns models from AWS Bedrock."""
# pylint: disable=import-error
# pylint: disable=no-name-in-module

import os
import boto3
from dotenv import load_dotenv
from langchain_aws import ChatBedrock
from langchain_aws import BedrockEmbeddings

load_dotenv()


def get_bedrock_models():
    """
    Initiates and returns models from AWS Bedrock.
    Returns:
        AzureChatOpenAI, AzureOpenAIEmbeddings, string: LLM, EMBEDDINGS_MODEL, "Azure OpenAI"
    """
    aws_session = boto3.Session(
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("AWS_SECRET_KEY"),
        region_name="eu-central-1",
    )

    bedrock_client = aws_session.client(service_name="bedrock-runtime")

    llm = ChatBedrock(
        model_id="eu.anthropic.claude-sonnet-4-5-20250929-v1:0",
        client=bedrock_client,
        model_kwargs={"temperature": 0.1},
    )

    embeddings_model = BedrockEmbeddings(
        client=bedrock_client, model_id="amazon.titan-embed-text-v2:0"
    )
    return llm, embeddings_model, "Amazon Web Services"
