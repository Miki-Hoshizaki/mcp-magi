# MAGI MCP Server

MCP Server implementation for MAGI code review system. This server provides a standardized interface for submitting code reviews and monitoring their progress using the Model Context Protocol (MCP).

## Features

- Code submission and review orchestration
- Integration with MAGI Gateway for distributed code review
- Multi-agent review system with Melchior, Balthasar, and Casper agents
- Majority-based decision making for code quality assessment

## Getting Started

### Prerequisites

- Python 3.11+
- Access to MAGI Gateway (default: ws://127.0.0.1:8000/ws)

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

The project consists of two main components:
1. MCP Server (`src/server.py`) - Implements the MCP protocol for code review
2. Test Client (`src/client.py`) - A simple client for testing the server functionality

### Running the Server

```bash
python -m src.server
```

By default, the server connects to the MAGI Gateway at `ws://127.0.0.1:8000/ws`. You can override this by setting the `MAGI_URL` environment variable:

```bash
MAGI_URL=ws://your-magi-gateway.com/ws python -m src.server
```

**Note: You can use the MAGI System official gateway:  `ws://magisystem.ai/ws`**

### Testing with the Client

The `client.py` script is provided as a testing tool to verify the MCP Server functionality. It is not intended for production use.

```bash
python -m src.client --file path/to/your/code.py
```

#### Client Options

- `--file`, `-f`: Path to the Python file to review
- `--magi-url`: MAGI Gateway WebSocket URL (default: ws://127.0.0.1:8000/ws)
- `--server-script`: Path to the server script (default: src/server.py)
- `--timeout`: Review timeout in seconds (default: 300)
- `--output`, `-o`: Save results to JSON file
- `--debug`: Enable debug mode

If no file is provided, the client will use an example code snippet for testing.

### Example

```bash
# Review a specific Python file
python -m src.client --file my_code.py

# Save review results to a file
python -m src.client --file my_code.py --output review_results.json

# Use a custom MAGI Gateway
python -m src.client --file my_code.py --magi-url ws://custom-gateway:8000/ws
```

### Example

```bash
(base) ➜  mcp-magi git:(main) ✗ python src/client.py 
2025-03-03 03:24:45,320 - magi-client - INFO - Creating MAGIClient...
2025-03-03 03:24:45,321 - magi-client - INFO - Using server script: /workspace/mcp-magi/src/server.py
2025-03-03 03:24:45,321 - magi-client - INFO - MAGI URL: ws://127.0.0.1:8000/ws
🚀 Starting MAGI Code Review...
2025-03-03 03:24:45,321 - magi-client - INFO - Starting code review...
2025-03-03 03:24:45,321 - magi-client - INFO - Starting stdio client...
2025-03-03 03:24:45,327 - magi-client - INFO - Initializing client session...
2025-03-03 03:24:45,564 - magi-client - INFO - Session initialized successfully
2025-03-03 03:24:45,565 - magi-client - INFO - Calling code_review tool...
INFO:mcp.server.lowlevel.server:Processing request of type CallToolRequest
WARNING:__main__:Received response for different request ID: None
WARNING:__main__:Received response for different request ID: None
2025-03-03 03:24:55,501 - magi-client - INFO - Code review completed successfully
2025-03-03 03:24:55,555 - magi-client - INFO - Review completed, printing results...

==================================================
MAGI CODE REVIEW RESULTS
==================================================

🎯 Final Decision: NEGATIVE
✅ Passed: False

📝 Detailed Reviews:
--------------------------------------------------

Reviewer melchior: I'll analyze this code from an architectural perspective.

Architectural Review:

1. Code Organization:
- The code follows a basic modular structure with separate function definitions
- There's a clear entry point with the `if __name__ == "__main__"` idiom
- Functions have single responsibilities, which aligns with SOLID principles

2. Design Patterns:
- The code implements a simple procedural pattern
- While basic, it demonstrates separation of concerns between calculation and program execution

3. Component Interactions:
- Clear data flow between functions
- Simple and predictable function interfaces
- Low coupling between components

4. Scalability & Maintainability:
- The code is easily maintainable due to its simplicity
- The `calculate_sum` function is reusable and independent
- Could benefit from type hints for better maintainability
- No error handling mechanisms in place

Recommendations:
1. Add type hints:
\```python
def calculate_sum(numbers: list[int]) -> int:
\```
2. Consider adding input validation
3. Could be enhanced with a proper exception handling strategy
4. Consider implementing an interface or class structure for more complex scenarios

<decision>POSITIVE</decision>

While the code is very basic, it follows good architectural principles:
- Clear separation of concerns
- Single responsibility principle
- Good modularization
- Clean interface between components

The code provides a solid foundation that could be easily extended while maintaining its architectural integrity. The simplicity here is actually a strength, as it doesn't over-engineer a straightforward solution.

Reviewer balthasar: I'll analyze this Python code from a security and stability perspective:

Security Analysis:
1. Input Validation:
- No input validation is performed on the 'numbers' parameter
- Could potentially accept non-numeric values leading to TypeErrors
- No bounds checking for potential integer overflow

2. Error Handling:
- No exception handling mechanisms
- Could crash if invalid input is provided
- No logging of errors or unexpected behavior

3. Data Protection:
- No sensitive data handling concerns in this simple example
- Variables are appropriately scoped

4. Stability Issues:
- No type hints to ensure correct input types
- No protection against large input arrays that could cause memory issues

Recommended Improvements:
\```python
from typing import List, Union
import logging

def calculate_sum(numbers: List[Union[int, float]]) -> Union[int, float]:
    try:
        if not numbers:
            return 0
        if not all(isinstance(x, (int, float)) for x in numbers):
            raise TypeError("All elements must be numbers")
        return sum(numbers)
    except Exception as e:
        logging.error(f"Error in calculate_sum: {str(e)}")
        raise

def main() -> None:
    try:
        numbers = [1, 2, 3, 4, 5]
        result = calculate_sum(numbers)
        print(f"The sum is: {result}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
\```

While the original code is functional for basic use cases, it lacks important security and stability features that would make it production-ready.

<decision>NEGATIVE</decision>

Reasons for negative decision:
1. Missing input validation
2. No error handling
3. No type checking
4. No logging mechanism
5. Potential for uncaught exceptions

The code needs significant improvements to meet security and stability standards for production use. While it may work for simple cases, it's not robust enough for handling edge cases or potential misuse.

Reviewer casper: I'll review this Python code focusing on functionality, implementation, and user experience aspects.

Code Review:

1. Functionality and Completeness:
- The code successfully implements a basic sum calculation function
- The main structure is properly organized with separate functions
- Includes proper `if __name__ == "__main__":` entry point
- Basic functionality is complete for the intended purpose

2. User Experience:
- Output message is clear and descriptive ("The sum is: ")
- However, lacks input validation for non-numeric values
- No error handling for empty lists or invalid inputs
- Could benefit from user interaction rather than hardcoded values

3. Performance and Efficiency:
- The implementation is simple and straightforward
- For small lists, the performance is acceptable
- Could use built-in `sum()` function for better performance
- Memory usage is minimal and efficient

4. Implementation Best Practices:
- Good function naming conventions
- Clear code structure
- Missing docstrings for function documentation
- No type hints which could improve code clarity

Suggestions for Improvement:
\```python
def calculate_sum(numbers: list[float]) -> float:
    """Calculate the sum of numbers in a list.
    
    Args:
        numbers: List of numbers to sum
    Returns:
        float: Sum of all numbers
    Raises:
        ValueError: If list is empty or contains non-numeric values
    """
    if not numbers:
        raise ValueError("List cannot be empty")
    return sum(numbers)

def main():
    try:
        numbers = [float(x) for x in input("Enter numbers separated by space: ").split()]
        result = calculate_sum(numbers)
        print(f"The sum is: {result}")
    except ValueError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
\```

<decision>POSITIVE</decision>

The code is fundamentally sound and achieves its basic purpose. While there's room for improvement in terms of error handling, user interaction, and documentation, the current implementation is functional and follows basic programming principles. The positive decision is based on the code's correct functionality and clear structure, though implementing the suggested improvements would make it more robust and user-friendly.

🤖 MAGI Agents State:
--------------------------------------------------

🔹 MELCHIOR:
  Decision: NEGATIVE
  Content: I'll analyze this code from an architectural perspective.

Architectural Review:

1. Code Organization:
- The code follows a basic modular structure with separate function definitions
- There's a clea...

🔹 BALTHASAR:
  Decision: NEGATIVE
  Content: I'll analyze this Python code from a security and stability perspective:

Security Analysis:
1. Input Validation:
- No input validation is performed on the 'numbers' parameter
- Could potentially acce...

🔹 CASPER:
  Decision: NEGATIVE
  Content: I'll review this Python code focusing on functionality, implementation, and user experience aspects.

Code Review:

1. Functionality and Completeness:
- The code successfully implements a basic sum ca...

✨ Review completed successfully!
```
## Architecture

The server acts as a bridge between MCP clients and the MAGI Gateway:

```
Test Client <-> MCP Server <-> MAGI Gateway <-> Review Agents (Melchior, Balthasar, Casper)
```

The review process:
1. Client submits code to the MCP Server
2. Server forwards the code to the MAGI Gateway
3. MAGI Gateway distributes the code to three review agents
4. Each agent reviews the code and provides a POSITIVE or NEGATIVE decision
5. The final decision is based on majority vote (at least 2 positive reviews to pass)
6. Results are returned to the client

## Development

For development purposes, you can enable debug logging:

```bash
DEBUG=1 python -m src.server
```

Or when using the client:

```bash
python -m src.client --file my_code.py --debug
```

## License

MIT License
