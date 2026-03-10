# Agentic Multi-Language Orchestrator (LangGraph & Pydantic)

## 🎯 Executive Overview
This project demonstrates a **Production-Grade Agentic Workflow** designed to bridge the gap between legacy systems (VBA) and modern data science stacks (Python, R). Using **LangGraph** for state management and **Azure OpenAI (GPT-4o-mini)** for reasoning, the orchestrator autonomously classifies business requirements and routes them to specialized agents for code generation.

**Business Value:** Automates the decision-making process for technology migration, ensuring that legacy automation (VBA) is only used when necessary, while promoting scalable Python/R architectures. It eliminates human error in tech stack selection.

---

## 🛠 Tech Stack & Engineering Standards
- **Framework:** `LangGraph` (Directed Acyclic Graphs with Cyclic State Management)
- **Validation:** `Pydantic v2` for Strict Structured Output and Type Safety
- **LLM:** `AzureChatOpenAI` (Integrated via **Poland Central** region for minimal latency)
- **Containerization:** `Docker` & `Docker Compose` for environment parity.
- **State Management:** `TypedDict` with `Annotated` message history for full traceability.

---

## 🏗 System Architecture (Agentic Design)
The system follows a **Modular Router-Agent Architecture**:

1. **Semantic Classifier (Node):** Performs trade-off analysis (VBA integration vs. Python scalability) using structured output.
2. **State-Based Router:** A conditional logic gate managing the flow between nodes based on the Classifier's intent.
3. **Specialized Reasoning Engines (Nodes):**
    * **Python Agent:** Optimized for scalable data engineering and ML.
    * **R Agent:** Tailored for advanced statistical modeling and visualization.
    * **VBA Agent:** Focused on MS Office integration and legacy automation.

---

## 🚀 Deployment & Usage

### Running with Docker (Recommended)
This is the fastest way to ensure environment consistency.

1. **Clone Repository**
    
     ```Bash
    git clone [https://github.com/aleksanderwasilewski1310/agentic_ai_tech_stack_evaluator.git](https://github.com/aleksanderwasilewski1310/agentic_ai_tech_stack_evaluator.git)
    cd agentic_ai_tech_stack_evaluator
    ```

1. **Environment Configuration:**

    Create a .env file with your Azure credentials:

    ```Code
    AZURE_OPENAI_ENDPOINT="your-endpoint"
    AZURE_OPENAI_DEPLOYMENT_NAME="your-deployment"
    AZURE_OPENAI_API_KEY="your-key"
    OPENAI_API_VERSION="2024-08-01-preview"
    ```

2. **Build the image:**
   ```bash
   docker compose build
    ```

3. **Run the interactive agent:**

    ```Bash
    docker run -it agentic_ai_tech_stack_evaluator-server
    ```

(Note: The -it flag is mandatory for interactive terminal sessions with the LLM agents.)

### Local Installation

1. **Clone & Install requirements:**

    ```Bash
    git clone [https://github.com/aleksanderwasilewski1310/agentic_ai_tech_stack_evaluator.git](https://github.com/aleksanderwasilewski1310/agentic_ai_tech_stack_evaluator.git)
    cd agentic_ai_tech_stack_evaluator
    pip install -r requirements.txt
    ```

2. **Environment Configuration:**

    Create a .env file with your Azure credentials:

    ```Code
    AZURE_OPENAI_ENDPOINT="your-endpoint"
    AZURE_OPENAI_DEPLOYMENT_NAME="your-deployment"
    AZURE_OPENAI_API_KEY="your-key"
    OPENAI_API_VERSION="2024-08-01-preview"
    ```

3. **Run the application:**
    ```Bash
    python main.py
    ```

## 🚦 Key Senior-Level Features

Hypothesis-Driven Routing: The classifier evaluates business heuristics before routing, preventing "model hallucinations" in stack choice.

Error-Resistant Design: Implementation of Pydantic models ensures the orchestrator never crashes due to unstructured LLM responses.

Production Hygiene: Isolated environment via Docker, ready for CI/CD and cloud-native deployment.

### 📈 Future Roadmap

[ ] LangSmith Integration: Trace monitoring and latency tracking for enterprise-scale auditing.

[ ] Groundedness Checks: Automated validation to prevent hallucinations in generated code snippets.

[ ] Cloud-Native Deployment: Transitioning to Azure Container Instances (ACI).

### Author: Aleksander Wasilewski – Senior Solutions Developer