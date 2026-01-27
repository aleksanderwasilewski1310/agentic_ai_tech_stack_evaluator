Markdown

# Agentic Multi-Language Orchestrator (LangGraph & Pydantic)

## 🎯 Executive Overview
This project demonstrates a **Production-Grade Agentic Workflow** designed to bridge the gap between legacy systems (VBA) and modern data science stacks (Python, R). Using **LangGraph** for state management and **Azure OpenAI (GPT-4o)** for reasoning, the orchestrator autonomously classifies business requirements and routes them to specialized agents for code generation.

**Business Value:** Automates the decision-making process for technology migration, ensuring that legacy automation (VBA) is only used when necessary, while promoting scalable Python/R architectures.

---

## 🛠 Tech Stack & Engineering Standards
- **Framework:** `LangGraph` (Cyclic Directed Acyclic Graphs for Agents)
- **Validation:** `Pydantic v2` for Strict Structured Output
- **LLM:** `AzureChatOpenAI` (Enterprise-grade integration)
- **State Management:** `TypedDict` with `Annotated` message history for full traceability.

---

## 🏗 System Architecture (Agentic Design)
The system follows a **Modular Router-Agent Architecture**:

1.  **Semantic Classifier (Node):** Uses structured output to perform a trade-off analysis between Python, R, and VBA based on predefined business heuristics.
2.  **State-Based Router:** A conditional logic gate that manages the flow between nodes based on the Classifier's intent.
3.  **Specialized Reasoning Engines (Nodes):**
    * **Python Agent:** Optimized for scalable data engineering and ML.
    * **R Agent:** Tailored for advanced statistical modeling and visualization.
    * **VBA Agent:** Focused on MS Office integration and legacy automation.

---

## 🚀 Key Senior-Level Features
* **Hypothesis-Driven Routing:** The classifier doesn't just "guess"; it evaluates pros/cons (VBA integration vs Python scalability) before routing.
* **Error-Resistant Design:** Implementation of **Pydantic models** ensures that the orchestrator never breaks due to unstructured LLM responses.
* **Engineering Hygiene:** Modular code structure ready for CI/CD integration and unit testing.

---

## 🚦 Getting Started

### Prerequisites
- Python 3.10+
- Azure OpenAI Instance

### Installation
```bash
git clone [https://github.com/aleksanderwasilewski1310/agentic_ai_tech_stack_evaluator.git](https://github.com/aleksanderwasilewski1310/agentic_ai_tech_stack_evaluator.git)
cd agentic-evaluator
pip install -r requirements.txt
Environment Configuration
Create a .env file (see .env.example):


ENDPOINT="your-endpoint"
DEPLOYMENT_ID="your-id"
API_VERSION="2024-02-15-preview"
API_KEY="your-key"
📈 Future Roadmap (Evaluation & Monitoring)
[ ] Integration with LangSmith for trace monitoring and latency tracking (as per Bayer's requirements).

[ ] Implementation of Groundedness Checks to prevent hallucinations in generated code.

[ ] Expansion to Cloud-Native Deployment (AWS Lambda / Azure Functions).

Author: Aleksander Wasilewski – Senior Solutions Developer
