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

1. **Build the image:**
   ```bash
   docker compose build