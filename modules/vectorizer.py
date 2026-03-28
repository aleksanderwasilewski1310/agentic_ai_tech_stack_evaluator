import re
from typing import List


def process_ai_response(raw_text: str) -> List[float]:
    """
    Parses the AI agent's response to separate code from descriptive text.

    This function extracts the programming language, the actual code content, 
    and generates a feature vector intended for a TensorFlow complexity model.
    It avoids using language-specific parsers like 'ast' to ensure compatibility 
    across different tech stacks (e.g., Python, VBA, SQL).

    Args:
        raw_text: The full string response received from the AI agent.

    Returns:
        A list contains complexity [Lines of Code, Logic Keywords, I/O Operations, Description Length].
    """

    # 1. Detect code block and language using Regex
    # Matches markdown code blocks: ```language ... code ... ```
    match = re.search(r"```(\w+)?\s+(.*?)```", raw_text,
                      re.DOTALL | re.IGNORECASE)

    if not match:
        # Return default values if no code block is found
        return [0.0, 0.0, 0.0, float(len(raw_text))]

    # Extract language (default to 'text') and clean up code content
    language = (match.group(1) or "text").lower()
    code_content = match.group(2).strip()

    # Extract description by removing the code block from the original text
    description = raw_text.replace(match.group(0), "").strip()

    # 2. Feature Engineering (Language-Agnostic)
    # We use regex instead of 'ast' to handle VBA, Python, and other languages without syntax errors.

    # Feature 1: Lines of Code (LOC)
    loc = len(code_content.splitlines())

    # Feature 2: Logic Keywords Density
    # Counts occurrences of keywords that imply logical complexity (conditional/loops/declarations)
    # Works for both Python (if, def) and VBA (if, sub, dim)
    logic_keywords = len(re.findall(
        r"\b(if|for|while|sub|def|class|dim|set|else|elif|then)\b", code_content, re.I))

    # Feature 3: I/O and System Operations
    # Identifies interactions with files, workbooks, or system paths (common complexity indicators)
    io_operations = len(re.findall(
        r"\b(open|save|connect|workbook|path|os\.|dir|file)\b", code_content, re.I))

    # Feature 4: Deployment Instruction Length
    # Longer descriptions often correlate with more complex setup or integration requirements
    desc_len = len(description)

    # 3. Final Feature Vector Construction
    # This vector [LOC, Logic, I/O, Desc_Len] will be fed into a TensorFlow regression model
    feature_vector = [float(loc), float(logic_keywords),
                      float(io_operations), float(desc_len)]

    return feature_vector
