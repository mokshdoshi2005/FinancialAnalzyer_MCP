from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional
import asyncio
import subprocess
import json
import os
from dotenv import load_dotenv

load_dotenv()

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
    params: Dict[str, Any]
    id: Optional[str] = "1"


# Store for MCP process
mcp_process = None


async def start_mcp_server():
    """Start the MCP server process"""
    global mcp_process
    if mcp_process is None:
        mcp_process = await asyncio.create_subprocess_exec(
            "python", "src/mcp_server.py",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
    return mcp_process


async def send_mcp_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Send request to MCP server"""
    process = await start_mcp_server()

    # Send JSON-RPC request
    request_json = json.dumps(request_data) + "\n"
    process.stdin.write(request_json.encode())
    await process.stdin.drain()

    # Read response
    response_line = await process.stdout.readline()
    if response_line:
        return json.loads(response_line.decode().strip())
    else:
        raise HTTPException(status_code=500, detail="No response from MCP server")


@app.on_event("startup")
async def startup_event():
    """Initialize MCP server on startup"""
    await start_mcp_server()


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "Financial Document Analyzer MCP Server",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "/analyze": "Quick document analysis",
            "/mcp": "MCP protocol endpoint",
            "/tools": "List available tools",
            "/health": "Health check"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "financial-document-analyzer"}


@app.post("/analyze")
async def analyze_document(request: DocumentAnalysisRequest):
    """Quick document analysis endpoint"""
    try:
        mcp_request = {
            "jsonrpc": "2.0",
            "id": "1",
            "method": "tools/call",
            "params": {
                "name": "analyze_financial_document",
                "arguments": {
                    "document_content": request.document_content,
                    "document_type": request.document_type
                }
            }
        }

        response = await send_mcp_request(mcp_request)
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/mcp")
async def handle_mcp_request(request: MCPRequest):
    """Handle raw MCP requests"""
    try:
        mcp_request = {
            "jsonrpc": "2.0",
            "id": request.id,
            "method": request.method,
            "params": request.params
        }

        response = await send_mcp_request(mcp_request)
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tools")
async def list_tools():
    """List available MCP tools"""
    try:
        mcp_request = {
            "jsonrpc": "2.0",
            "id": "1",
            "method": "tools/list",
            "params": {}
        }

        response = await send_mcp_request(mcp_request)
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("SERVER_PORT", 8000))
    host = os.getenv("SERVER_HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port)