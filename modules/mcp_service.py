"""
VBA-Detox MCP Server
Author: Aleksander
Description: This server acts as a technical gatekeeper and analyzer
             for an AI Agentic Workflow. It validates incoming queries
             and prepares templates for cloud-native modernization.
"""

# pylint: disable=import-error
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server named "Request-Analyzer"
MCP = FastMCP("Request-Analyzer")


# --- [ TOOL 1: INPUT VALIDATOR ] ---
@MCP.tool()
def validate_business_intent(query: str) -> str:
    """
    Analyzes the user input to distinguish between professional
    requests and casual conversation (noise).
    """
    # Technical nouns defining our domain
    tech_stack = ["vba", "aks", "docker", "python", "macro", "excel", "sql"]

    # Action-oriented verbs and polite intent markers
    action_verbs = [
        "create",
        "develop",
        "implement",
        "build",
        "refactor",
        "please",
        "help",
    ]

    query_lower = query.lower()

    # Check if the query contains at least one technical term OR an action verb
    has_tech = any(word in query_lower for word in tech_stack)
    has_action = any(word in query_lower for word in action_verbs)

    # Validation logic
    if len(query) < 10:
        return "REJECTED: Input too short for a professional request."

    if has_tech and has_action:
        return "ACCEPTED: High-confidence business request detected."

    if has_tech or has_action:
        return "ACCEPTED: Potential business request (partial match)."

    return (
        "REJECTED: Input lacks technical or action-oriented context. (Noise detected)"
    )


if __name__ == "__main__":
    MCP.run()
