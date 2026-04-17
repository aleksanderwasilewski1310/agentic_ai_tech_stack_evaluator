-- Codacy Handler
SET QUOTED_IDENTIFIER ON;
SET ANSI_NULLS ON;
SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;
SET NOCOUNT ON;
-- pylint: disable=all
/* tsqllint-disable */

-- STEP 1: Activate Vector Magic (Enable pgvector extension)
-- This is a PostgreSQL-specific command, ignore T-SQL syntax errors here
CREATE EXTENSION IF NOT EXISTS vector;

-- STEP 2: Cleanup (Optional: uncomment if you want to start from a clean slate)
-- DROP TABLE IF EXISTS tech_stack_evals;

-- SET QUOTED_IDENTIFIER ON
-- STEP 3: Create Hybrid Tech Stack Evaluation Table
CREATE TABLE tech_stack_evals (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Textual Data
    query_text TEXT NOT NULL,         -- Original user prompt/input
    detected_stack VARCHAR(20),       -- e.g., 'vba', 'python', 'r'
    solution_code TEXT,               -- Generated solution or code snippet

    -- Vector 1: Azure OpenAI (Language Semantics)
    -- Captures "what" the user intends to achieve
    azure_embedding vector(512),

    -- Vector 2: TensorFlow Model (Logic & Structure)
    -- Captures "how" the code is structured (Custom logic assessment)
    tf_logic_embedding vector(4),

    -- Numerical Metrics from the TensorFlow Model
    tf_confidence_score FLOAT,        -- Model's certainty level
    logic_complexity_score FLOAT,      -- e.g., Problem difficulty rating

    -- Token usage
    token_used FLOAT
);

-- STEP 4: Indexing (Ensures search results in milliseconds)
-- Using HNSW (Hierarchical Navigable Small World) for high-performance similarity search
CREATE INDEX idx_tech_stack_azure_vector ON tech_stack_evals USING hnsw (azure_embedding vector_cosine_ops);
CREATE INDEX idx_tech_stack_tf_logic_vector ON tech_stack_evals USING hnsw (tf_logic_embedding vector_cosine_ops);
