"""Module for managing PostgreSQL database connections for AI agent data."""

# pylint: disable=import-error
import logging
import os
import psycopg2
from dotenv import load_dotenv
from pgvector.psycopg2 import register_vector
import numpy as np

# Logger configuration
LOGGER = logging.getLogger("AI-Agent.DB")

load_dotenv()


def push_ai_data_to_db(ai_data):
    """
    Combines results from two AI models and saves them to PostgreSQL.
    Args:
    ai_data - Dictionary of data received from AI
    """
    conn = None
    cur = None
    query = ai_data["query"]
    stack = ai_data["stack"]
    code = ai_data["code"]
    azure_vec = ai_data["azure_vec"]
    tf_model_output = ai_data["tf_model_output"]
    tokens_used = ai_data["tokens_used"]
    try:
        LOGGER.info("Attempting to store AI data in the Vault...")
        # 1. Connection (note the port 5433!)
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "db"),
            port=os.getenv("DB_PORT", "5432"),
            database=os.getenv("DB_NAME", "postgres"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASS", "password"),
        )
        register_vector(conn)
        cur = conn.cursor()

        # 2. Prepare TensorFlow data
        # Extract the vector and a sample confidence score
        tf_vector = tf_model_output
        confidence = float(np.max(tf_vector))

        # 3. SQL INSERT
        insert_query = """
        INSERT INTO tech_stack_evals (
            query_text, detected_stack, solution_code, 
            azure_embedding, tf_logic_embedding, tf_confidence_score, token_used
        ) VALUES (%s, %s, %s, %s, %s, %s, %s);
        """

        cur.execute(
            insert_query,
            (query, stack, code, azure_vec, tf_vector, confidence, tokens_used),
        )

        conn.commit()
        LOGGER.info("✅ Successfully stored result for stack: %s (Confidence: %.2f)",
                    stack.upper(), confidence)
    except psycopg2.Error as error:
        LOGGER.error("❌ PostgreSQL error during insert: %s", error)
    except Exception as error: # pylint: disable=broad-except
        LOGGER.error("❌ Unexpected error during DB push: %s", error)
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def find_similar_query_and_distance(query_embedding, threshold=0.1):
    """
    Searches the database for a similar query using vector similarity.
    Uses pgvector's cosine distance operator (<=>).
    Distance = 1 - Cosine Similarity.
    Threshold 0.1 means we accept matches with >90% similarity.
    """
    conn = None
    cur = None
    similar_solution = None
    distance = None

    try:
        LOGGER.info("Connecting to DB for semantic search (threshold: %.2f)...", threshold)

        # Establish connection using environment variables
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "db"),
            port=os.getenv("DB_PORT", "5432"),
            database=os.getenv("DB_NAME", "postgres"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASS", "password"),
        )
        # Required to handle vector types in psycopg2
        register_vector(conn)
        cur = conn.cursor()

        # SQL query to find the closest match based on Azure embeddings
        # We select the solution and the distance
        search_query = """
        SELECT solution_code, (azure_embedding <=> %s::vector) AS distance
        FROM tech_stack_evals
        WHERE (azure_embedding <=> %s::vector) < %s
        ORDER BY distance ASC
        LIMIT 1;
        """

        # Execute search with the provided embedding and threshold
        cur.execute(search_query, (query_embedding, query_embedding, threshold))
        result = cur.fetchone()

        if result:
            similar_solution = result[0]
            distance = result[1]
            LOGGER.info("🔍 Semantic Cache HIT! Distance: %.4f", distance)
        else:
            LOGGER.info("⚪ Semantic Cache MISS - no similar queries found.")
    except psycopg2.Error as error:
        LOGGER.error("❌ PostgreSQL error during search: %s", error)
    except Exception as error: # pylint: disable=broad-except
        LOGGER.error("❌ Unexpected error during semantic search: %s", error)
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

    return similar_solution, distance
