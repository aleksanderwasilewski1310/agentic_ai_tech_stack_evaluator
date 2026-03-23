import psycopg2
from dotenv import load_dotenv
from pgvector.psycopg2 import register_vector
import numpy as np
import tensorflow as tf
import os

load_dotenv()

def push_ai_data_to_db(query, stack, code, azure_vec, tf_model_output):
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
            password=os.getenv("DB_PASS", "password")
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
            azure_embedding, tf_logic_embedding, tf_confidence_score
        ) VALUES (%s, %s, %s, %s, %s, %s);
        """
        
        cur.execute(insert_query, (
            query, stack, code, 
            azure_vec, tf_vector, confidence
        ))

        conn.commit()
        print("✅ AI Data (Azure + TensorFlow) successfully stored in the Vault!")

    except Exception as e:
        print(f"❌ Database insert error: {e}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
