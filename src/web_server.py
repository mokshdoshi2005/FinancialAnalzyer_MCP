from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any, Optional
import asyncio
import subprocess
import json
import os
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Financial Document Analyzer MCP Server",
    description="MCP server for AI-powered financial document analysis",
    version="1.0.0"
)


class DocumentAnalysisRequest(BaseModel):
    document_content: str
    document_type: Optional[str] = "auto_detect"


class MCPRequest(BaseModel):
    method: str
    params: Optional[Dict[str, Any]] = {}
    id: Optional[str] = "1"


class MCPServerManager:
    def __init__(self):
        self.process = None
        self.initialized = False

    async def ensure_running(self):
        """Ensure MCP server is running and initialized"""
        if self.process is None:
            # Start the process
            self.process = await asyncio.create_subprocess_exec(
                sys.executable, "src/mcp_server.py",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.path.dirname(os.path.dirname(__file__))
            )
            logger.info("MCP server process started")

        if not self.initialized:
            # Send initialization request
            await self.initialize_server()

    async def initialize_server(self):
        """Initialize the MCP server"""
        init_request = {
            "jsonrpc": "2.0",
            "id": "init",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "clientInfo": {
                    "name": "financial-doc-web-server",
                    "version": "1.0.0"
                }
            }
        }

        try:
            response = await self.send_raw_request(init_request)
            logger.info(f"Initialization response: {response}")

            # Send initialized notification
            initialized_request = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized"
            }
            await self.send_raw_request(initialized_request, expect_response=False)

            self.initialized = True
            logger.info("MCP server initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize MCP server: {e}")
            raise

    async def send_raw_request(self, request_data: Dict[str, Any], expect_response: bool = True) -> Optional[
        Dict[str, Any]]:
        """Send raw request to MCP server"""
        try:
            request_json = json.dumps(request_data) + "\n"
            self.process.stdin.write(request_json.encode())
            await self.process.stdin.drain()

            if expect_response:
                response_line = await asyncio.wait_for(
                    self.process.stdout.readline(),
                    timeout=10.0
                )

                if response_line:
                    response_text = response_line.decode().strip()
                    if response_text:  # Only parse non-empty responses
                        return json.loads(response_text)

            return None

        except asyncio.TimeoutError:
            logger.error("Timeout waiting for MCP server response")
            raise HTTPException(status_code=504, detail="MCP server timeout")
        except Exception as e:
            logger.error(f"MCP communication error: {e}")
            raise HTTPException(status_code=500, detail=f"MCP error: {str(e)}")

    async def send_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send request with proper initialization"""
        await self.ensure_running()

        # Ensure proper JSON-RPC format
        if "jsonrpc" not in request_data:
            request_data["jsonrpc"] = "2.0"
        if "id" not in request_data:
            request_data["id"] = "1"
        if "params" not in request_data:
            request_data["params"] = {}

        return await self.send_raw_request(request_data)


# Global manager
mcp_manager = MCPServerManager()


@app.on_event("startup")
async def startup_event():
    """Startup event"""
    logger.info("Starting web server...")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    if mcp_manager.process:
        mcp_manager.process.terminate()
        await mcp_manager.process.wait()


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Financial Document Analyzer MCP Server",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "/analyze": "Quick document analysis",
            "/mcp": "Raw MCP requests",
            "/tools": "List available tools",
            "/health": "Health check",
            "/test": "Test MCP connection"
        }
    }


@app.get("/health")
async def health_check():
    """Health check"""
    try:
        await mcp_manager.ensure_running()
        return {
            "status": "healthy",
            "service": "financial-document-analyzer",
            "mcp_initialized": mcp_manager.initialized
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@app.get("/test")
async def test_mcp():
    """Test MCP connection"""
    try:
        await mcp_manager.ensure_running()
        return {
            "status": "MCP server is running and initialized",
            "initialized": mcp_manager.initialized
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MCP test failed: {str(e)}")


@app.get("/tools")
async def list_tools():
    """List available tools"""
    try:
        request = {
            "jsonrpc": "2.0",
            "id": "tools-list",
            "method": "tools/list",
            "params": {}
        }

        response = await mcp_manager.send_request(request)
        return response

    except Exception as e:
        logger.error(f"Tools list error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list tools: {str(e)}")


@app.post("/mcp")
async def handle_mcp_request(request: MCPRequest):
    """Handle raw MCP requests"""
    try:
        request_data = {
            "jsonrpc": "2.0",
            "id": request.id,
            "method": request.method,
            "params": request.params or {}
        }

        response = await mcp_manager.send_request(request_data)
        return response

    except Exception as e:
        logger.error(f"MCP request error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze")
async def analyze_document(request: DocumentAnalysisRequest):
    """Quick document analysis"""
    try:
        mcp_request = {
            "jsonrpc": "2.0",
            "id": "analyze",
            "method": "tools/call",
            "params": {
                "name": "analyze_financial_document",
                "arguments": {
                    "document_content": request.document_content,
                    "document_type": request.document_type
                }
            }
        }

        response = await mcp_manager.send_request(mcp_request)
        return response

    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
