"""
MAGI MCP Server - Core Server Module
This module implements the main MCP server functionality for code review orchestration.
"""

from mcp.server.fastmcp import FastMCP, Context
from typing import Dict, Any, Literal, Optional
import websockets
import json
import logging
import os
import hashlib
import asyncio
from datetime import datetime
import uuid
import time

# Configure logging
if os.getenv("DEBUG", "0") == "1":
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MAGI Gateway Constants
APP_ID = "b75fce6f-e8af-4207-9c32-f8166afb4520"
APP_SECRET = "magi-gateway-development-secret"
AGENT_IDS = [
    ("melchior", "d37c1cc8-bcc4-4b73-9f49-a93a30971f2c"),
    ("balthasar", "6634d0ec-d700-4a92-9066-4960a0f11927"),
    ("casper", "89cbe912-25d0-47b0-97da-b25622bfac0d"),
]

class MAGIDecision:
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"

class MAGIServer:
    def __init__(self, magi_url: str = "ws://127.0.0.1:8000/ws"):
        self.mcp = FastMCP("MAGI Code Review")
        self.name = "MAGI Code Review"
        self.magi_url = magi_url
        self._setup_tools()

    def _generate_auth_token(self) -> str:
        """Generate authentication token for MAGI Gateway"""
        current_minute = int(time.time() // 60)
        raw_str = f"{APP_ID}{APP_SECRET}{current_minute}"
        token_hash = hashlib.sha256(raw_str.encode()).hexdigest()
        return token_hash[:10]

    async def _connect_magi(self) -> str:
        """Connect to MAGI Gateway with authentication"""
        token = self._generate_auth_token()
        url = f"{self.magi_url}?appid={APP_ID}&token={token}"
        return url

    def _setup_tools(self):
        @self.mcp.tool()
        async def code_review(ctx: Context, user_input: str, code: str) -> Dict[str, Any]:
            """Submit code for MAGI review"""
            logger.debug("Submitting code for MAGI review")
            
            request_id = str(uuid.uuid4())
            magi_state = {
                "melchior": {"messages": [], "decision": None, "content": ""},
                "balthasar": {"messages": [], "decision": None, "content": ""},
                "casper": {"messages": [], "decision": None, "content": ""}
            }
            
            # Prepare review request
            review_request = {
                "type": "agent_judgement",
                "request_id": request_id,
                "request": f"<user_input>\n{user_input}\n</user_input>\n<response>\n{code}\n</response>",
                "timestamp": datetime.utcnow().timestamp(),
                "agents": [{"agent_id": agent_id} for _, agent_id in AGENT_IDS]
            }

            ws_url = await self._connect_magi()
            reviews = []
            completed_agents = set()
            final_result = ""
            passed = False

            async with websockets.connect(ws_url) as websocket:
                # Send review request
                logger.debug(f"Connecting to MAGI Gateway at {ws_url}")
                logger.debug(f"Sending review request with ID: {request_id}")
                await websocket.send(json.dumps(review_request))
                logger.debug("Review request sent successfully")

                while True:
                    try:
                        logger.debug("Waiting for response from MAGI Gateway...")
                        message = await websocket.recv()
                        response = json.loads(message)
                        logger.debug(f"Received response: {response}")

                        if response.get("request_id") != request_id:
                            logger.warning(f"Received response for different request ID: {response.get('request_id')}")
                            continue

                        msg_type = response.get("type")
                        if msg_type == "agent_response":
                            agent_id = response.get("agent_id")
                            agent_name = next((name for name, aid in AGENT_IDS if aid == agent_id), "unknown")
                            content = response.get("content", "")
                            status = response.get("status")
                            logger.debug(f"Received agent response from {agent_name}, status: {status}")

                            # Update agent state
                            agent_state = magi_state[agent_name]
                            agent_state["content"] += content
                            agent_state["messages"].append({
                                "request_id": request_id,
                                "content": content,
                                "timestamp": datetime.utcnow().isoformat()
                            })

                            if status == "completed":
                                completed_agents.add(agent_name)
                                agent_state["decision"] = (
                                    MAGIDecision.POSITIVE if "POSITIVE" in content 
                                    else MAGIDecision.NEGATIVE
                                )
                                logger.debug(f"Agent {agent_name} completed with decision: {agent_state['decision']}")

                                # Check if all agents have completed
                                if len(completed_agents) >= 3:
                                    # Count positive decisions
                                    positive_count = sum(
                                        1 for state in magi_state.values() 
                                        if state["decision"] == MAGIDecision.POSITIVE
                                    )
                                    
                                    passed = positive_count >= 2
                                    final_result = MAGIDecision.POSITIVE if passed else MAGIDecision.NEGATIVE
                                    logger.debug(f"All agents completed. Positive count: {positive_count}, Final result: {final_result}")
                                    break

                    except websockets.exceptions.ConnectionClosed:
                        logger.error("WebSocket connection closed")
                        break
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                        break

            # Collect reviews from all agents
            for agent_name, state in magi_state.items():
                reviews.append(f"Reviewer {agent_name}: {state['content']}")
            
            result = {
                "reviews": reviews,
                "result": final_result,
                "passed": passed,
                "magi_state": magi_state,
                "code": code
            }
            logger.debug(f"Returning result: {result}")
            return result

    def run(self):
        """Run the MCP server"""
        self.mcp.run()


if __name__ == "__main__":
    app = MAGIServer(
    magi_url=os.getenv("MAGI_URL", "ws://127.0.0.1:8000/ws")
)
    
    app.run()
