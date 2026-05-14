"""Unit tests for mcp_service module"""

import pytest

try:
    from modules.mcp_service import validate_business_intent
except ImportError:
    # Fallback for different execution contexts
    import sys
    import os

    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from modules.mcp_service import validate_business_intent


@pytest.mark.parametrize(
    "query, expected_status",
    [
        # Positive cases: Tech keywords + Action verbs
        ("Please help me create a VBA macro for Excel", "ACCEPTED"),
        ("I need to develop a new Docker container for AKS", "ACCEPTED"),
        ("Implement a Python script to automate SQL reports", "ACCEPTED"),
        # Borderline cases: Just tech or just action
        ("How to fix an Excel error?", "ACCEPTED"),  # Partial match
        ("Can you help me with this refactor?", "ACCEPTED"),  # Partial match
        # Negative cases: Noise / Casual talk
        ("Ann has a cat", "REJECTED"),
        ("What's the weather like in Warsaw?", "REJECTED"),
        ("Hi, how are you today?", "REJECTED"),
        # Edge cases: Too short
        ("vba fix", "REJECTED"),  # Too short even if tech keywords exist
        ("", "REJECTED"),  # Empty string
    ],
)
def test_validate_business_intent(query, expected_status):
    """
    Test if the validator correctly filters business intent
    from general noise.
    """
    result = validate_business_intent(query)
    assert expected_status in result
