import pytest

# Standard import - will work if pytest is run from the root directory
# and 'modules' contains an __init__.py file.
try:
    from modules.vectorizer import process_ai_response
except ImportError:
    # Fallback for different execution contexts
    import sys
    import os

    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from modules.vectorizer import process_ai_response


def test_process_ai_response_python():
    """Test case for a standard Python code block."""
    python_input = """
    Here is a simple script:
    ```python
    def calculate_sum(data):
        total = 0
        for item in data:
            total += item
        return total
    ```
    """
    vector = process_ai_response(python_input)
    assert vector[0] == 5.0  # LOC
    assert vector[1] == 2.0  # def, for


def test_process_ai_response_vba():
    """Test case for a legacy VBA code block."""
    vba_input = """
    ```vba
    Sub Update()
        Dim i As Integer
        For i = 1 To 10
            If i > 5 Then Exit For
        Next i
    End Sub
    ```
    """
    vector = process_ai_response(vba_input)
    assert vector[0] == 6.0
    assert vector[1] >= 4.0  # Sub, Dim, For, If


def test_process_ai_response_no_code():
    """Test case for responses without code blocks."""
    text_input = "No code here."
    vector = process_ai_response(text_input)
    assert vector[0] == 0.0
    assert vector[3] == float(len(text_input))
