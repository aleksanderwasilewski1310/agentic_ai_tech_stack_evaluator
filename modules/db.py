"""Module for managing PostgreSQL database connections for AI agent data."""
import os
import psycopg2
from dotenv import load_dotenv
from pgvector.psycopg2 import register_vector  # pylint: disable=import-error
import numpy as np

load_dotenv()


def push_ai_data_to_db(query, stack, code, azure_vec, tf_model_output, tokens_used):
    """
    Combines results from two AI models and saves them to PostgreSQL.
    """
    conn = None
    cur = None
    try:
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
        print("✅ AI Data (Azure + TensorFlow) successfully stored in the Vault!")

    except Exception as error:
        print(f"❌ Database insert error: {error}")
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
            print(f"🔍 Semantic Cache Hit! Found match with distance: {distance:.4f}")
        else:
            print("⚪ No similar query found in Semantic Cache.")

    except Exception as error:
        print(f"❌ Database search error: {error}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

    return similar_solution, distance
