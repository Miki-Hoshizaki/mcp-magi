from mcp import ClientSession
from mcp.client.sse import sse_client
import asyncio
import os
import sys
import json
import logging
import traceback
from typing import Dict, Any, Optional
import argparse

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('magi-client')

class MAGIClient:
    def __init__(self,
                sse_url: str = "http://127.0.0.1:8000/sse",
                debug: bool = False):
        logger.info(f"MAGI URL: {sse_url}")
        
        # Set environment variables
        env = os.environ.copy()  # Copy current environment variables
        env.update({
            "PYTHONUNBUFFERED": "1"  # Ensure output is not buffered
        })
        
        if debug:
            env["DEBUG"] = "1"
            
        self.sse_url = sse_url
        self.debug = debug
        self._session_context = None
        self._streams_context = None
        self.session = None

    async def _connect_to_sse_server(self):
        """Connect to MCP SSE server"""
        logger.info(f"Connecting to SSE server at {self.sse_url}...")
        
        # Store the context managers so they stay alive
        self._streams_context = sse_client(url=self.sse_url)
        streams = await self._streams_context.__aenter__()

        self._session_context = ClientSession(*streams)
        self.session = await self._session_context.__aenter__()

        # Initialize
        await self.session.initialize()
        logger.info("Session initialized successfully")

    async def _cleanup(self):
        """Properly clean up the session and streams"""
        if self._session_context:
            await self._session_context.__aexit__(None, None, None)
        if self._streams_context:
            await self._streams_context.__aexit__(None, None, None)

    async def review_code(self, code: str, user_input: str, timeout: float = 300) -> Dict[str, Any]:
        """
        Submit code for MAGI review
        
        Args:
            code: Code to be reviewed
            user_input: Description or context of the code
            timeout: Maximum time to wait for review (seconds)
        
        Returns:
            Dictionary containing review results
        """
        if self.debug:
            logger.info("Code to review:")
            logger.info("-" * 40)
            logger.info(code[:500] + "..." if len(code) > 500 else code)
            logger.info("-" * 40)
        
        try:
            logger.info("Connecting to SSE server...")
            await self._connect_to_sse_server()
            
            try:
                logger.info("Calling code_review tool...")
                try:
                    result = await asyncio.wait_for(
                        self.session.call_tool(
                            "code_review",
                            {
                                "user_input": user_input,
                                "code": code
                            }
                        ),
                        timeout=timeout
                    )
                    logger.info("Code review completed successfully")
                    # Debug log the raw result
                    logger.debug(f"Raw result: {result}")
                    
                    # Convert CallToolResult to dictionary if necessary
                    if hasattr(result, "model_dump"):
                        # For newer Pydantic v2.x
                        logger.debug("Converting result using model_dump()")
                        return result.model_dump()
                    elif hasattr(result, "dict"):
                        # For older Pydantic v1.x
                        logger.debug("Converting result using dict()")
                        return result.dict()
                    elif hasattr(result, "__dict__"):
                        # Fallback for regular Python objects
                        logger.debug("Converting result using __dict__")
                        return result.__dict__
                    else:
                        # Last resort - assume it's already dictionary-like
                        logger.debug("Converting result using dict()")
                        result_dict = dict(result)
                        logger.debug(f"Converted result: {result_dict}")
                        return result_dict
                except asyncio.TimeoutError:
                    logger.error(f"Review timed out after {timeout} seconds")
                    raise TimeoutError(f"Code review timed out after {timeout} seconds")
            finally:
                await self._cleanup()
        except asyncio.TimeoutError:
            raise
        except Exception as e:
            logger.error(f"Error during code review: {e}")
            logger.error(traceback.format_exc())
            raise

    def print_review_results(self, result: Dict[str, Any], output_file: Optional[str] = None):
        """
        Beautify review results output and optionally save to file
        
        Args:
            result: Review result dictionary
            output_file: Optional path to save results (JSON format)
        """
        print("\n" + "="*50)
        print("MAGI CODE REVIEW RESULTS")
        print("="*50)
        
        decision_value = result.get('result', 'N/A')
            
        print(f"\n🎯 Final Decision: {decision_value}")
        print(f"✅ Passed: {result.get('passed', False)}")
        
        print("\n📝 Detailed Reviews:")
        print("-"*50)
        for review in result.get('reviews', []):
            print(f"\n{review}")
        
        print("\n🤖 MAGI Agents State:")
        print("-"*50)
        for agent, state in result.get('magi_state', {}).items():
            print(f"\n🔹 {agent.upper()}:")
            print(f"  Decision: {state.get('decision', 'N/A')}")
            content = state.get('content', '')
            content_preview = content[:200] + "..." if len(content) > 200 else content
            print(f"  Content: {content_preview}")

        if output_file:
            try:
                with open(output_file, 'w') as f:
                    json.dump(result, f, indent=2)
                print(f"\n💾 Results saved to: {output_file}")
            except Exception as e:
                print(f"Warning: Failed to save results to file: {e}", file=sys.stderr)

async def main():
    """Main entry point with command line argument handling"""
    parser = argparse.ArgumentParser(description='MAGI Code Review Client')
    parser.add_argument('--file', '-f', help='Python file to review')
    parser.add_argument('--sse-url', default="http://127.0.0.1:8000/sse",
                       help='MAGI MCP Server SSE URL')
    parser.add_argument('--timeout', type=float, default=300,
                       help='Review timeout in seconds')
    parser.add_argument('--output', '-o', help='Save results to JSON file')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)
        logging.getLogger('websockets').setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")

    # If no file is provided, use example code
    example_code = """
def calculate_sum(numbers):
    total = 0
    for num in numbers:
        total += num
    return total

def main():
    numbers = [1, 2, 3, 4, 5]
    result = calculate_sum(numbers)
    print(f"The sum is: {result}")

if __name__ == "__main__":
    main()
    """

    code_to_review = example_code
    if args.file:
        try:
            logger.info(f"Reading code from file: {args.file}")
            with open(args.file, 'r') as f:
                code_to_review = f.read()
            logger.info(f"Successfully read {len(code_to_review)} bytes from file")
        except Exception as e:
            logger.error(f"Error reading file {args.file}: {e}")
            print(f"Error reading file {args.file}: {e}", file=sys.stderr)
            sys.exit(1)

    user_input = f"Please review this Python code: {args.file if args.file else 'example code'}"

    try:
        logger.info("Creating MAGIClient...")
        client = MAGIClient(
            sse_url=args.sse_url,
            debug=args.debug
        )
    except FileNotFoundError as e:
        logger.error(f"Server script not found: {e}")
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to initialize client: {e}")
        logger.error(traceback.format_exc())
        print(f"Error: Failed to initialize client: {e}", file=sys.stderr)
        sys.exit(1)

    print("🚀 Starting MAGI Code Review...")
    try:
        logger.info("Starting code review...")
        result = await client.review_code(
            code_to_review, 
            user_input,
            timeout=args.timeout
        )
        logger.info("Review completed, printing results...")
        # convert result
        data = json.loads(result['content'][0]['text'])
        client.print_review_results(data, output_file=args.output)
        print("\n✨ Review completed successfully!")
    except TimeoutError as e:
        logger.error(f"Review timed out: {e}")
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Review failed: {e}")
        logger.error(traceback.format_exc())
        print(f"❌ Review failed: {e}", file=sys.stderr)
        print("\nFor more details, run with --debug flag")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())