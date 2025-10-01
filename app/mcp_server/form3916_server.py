#!/usr/bin/env python3
"""
MCP Server for Form 3916
Exposes form processing capabilities via Model Context Protocol
"""

import asyncio
import json
import logging
import sys
import base64
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.packs.form_3916.graph_modern import (
    create_modern_form3916_graph,
    Form3916StateModern
)
from app.tools.document_parser import extract_text_from_file

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Form3916MCPServer:
    """MCP Server for Form 3916 processing"""

    def __init__(self):
        self.graph = create_modern_form3916_graph(use_checkpointer=False)
        self.current_state: Optional[Dict[str, Any]] = None
        self.session_id = None

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Main request handler for JSON-RPC"""

        method = request.get("method", "")
        params = request.get("params", {})
        request_id = request.get("id", 1)  # Default to 1 if no id provided

        try:
            # Route to appropriate handler
            if method == "initialize":
                result = await self.initialize(params)
            elif method == "initialized":
                # MCP protocol notification - just acknowledge
                result = {}
            elif method == "tools/list":
                result = self.list_tools()
            elif method == "tools/call":
                result = await self.call_tool(params)
            elif method == "resources/list":
                result = self.list_resources()
            elif method == "resources/read":
                result = await self.read_resource(params)
            elif method == "notifications/initialized":
                # Another MCP notification
                result = {}
            else:
                raise ValueError(f"Unknown method: {method}")

            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }

        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }

    async def initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize the MCP server"""

        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
                "resources": {}
            },
            "serverInfo": {
                "name": "form3916-server",
                "version": "1.0.0"
            }
        }

    def list_tools(self) -> Dict[str, Any]:
        """List available tools"""

        return {
            "tools": [
                {
                    "name": "form3916_extract",
                    "description": "Extract data from documents for Form 3916",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "documents": {
                                "type": "array",
                                "description": "Base64 encoded documents",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "content": {"type": "string", "description": "Base64 encoded content"}
                                    },
                                    "required": ["name", "content"]
                                }
                            },
                            "user_context": {
                                "type": "string",
                                "description": "Additional context from user"
                            }
                        },
                        "required": ["documents"]
                    }
                },
                {
                    "name": "form3916_complete",
                    "description": "Complete Form 3916 with user-provided data",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "user_data": {
                                "type": "object",
                                "description": "User data to complete the form",
                                "properties": {
                                    "date_naissance": {"type": "string"},
                                    "lieu_naissance": {"type": "string"},
                                    "adresse_complete": {"type": "string"},
                                    "lieu_signature": {"type": "string"},
                                    "date_cloture": {"type": "string"}
                                }
                            },
                            "skip_optional": {
                                "type": "boolean",
                                "description": "Skip optional fields",
                                "default": False
                            }
                        },
                        "required": ["user_data"]
                    }
                },
                {
                    "name": "form3916_generate",
                    "description": "Generate the final Form 3916 PDF",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "format": {
                                "type": "string",
                                "enum": ["base64", "url"],
                                "default": "base64",
                                "description": "Output format for the PDF"
                            }
                        }
                    }
                },
                {
                    "name": "form3916_status",
                    "description": "Get current processing status",
                    "inputSchema": {
                        "type": "object",
                        "properties": {}
                    }
                }
            ]
        }

    async def call_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool"""

        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name == "form3916_extract":
            return await self.extract_from_documents(arguments)
        elif tool_name == "form3916_complete":
            return await self.complete_with_user_data(arguments)
        elif tool_name == "form3916_generate":
            return await self.generate_pdf(arguments)
        elif tool_name == "form3916_status":
            return self.get_status()
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    async def extract_from_documents(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data from uploaded documents"""

        documents = arguments.get("documents", [])
        user_context = arguments.get("user_context", "")

        # Decode documents from base64
        input_files = []
        for doc in documents:
            name = doc["name"]
            content = base64.b64decode(doc["content"])
            input_files.append({name: content})

        # Initialize state
        self.current_state = {
            "input_files": input_files,
            "user_context": user_context,
            "classified_docs": [],
            "extracted_data_list": [],
            "consolidated_data": {},
            "missing_critical": [],
            "missing_optional": [],
            "skip_optional": False,
            "pdf_data": None,
            "generated_pdf": None
        }

        # Run extraction workflow
        try:
            result = await self.graph.ainvoke(self.current_state)
            self.current_state = result

            return {
                "content": [
                    {
                        "type": "text",
                        "text": self._format_extraction_result(result)
                    }
                ]
            }
        except Exception as e:
            logger.error(f"Extraction error: {e}")
            raise

    async def complete_with_user_data(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Complete form with user-provided data"""

        if not self.current_state:
            raise ValueError("No active session. Please extract documents first.")

        user_data = arguments.get("user_data", {})
        skip_optional = arguments.get("skip_optional", False)

        # Update consolidated data
        consolidated = self.current_state.get("consolidated_data", {})
        consolidated.update(user_data)
        self.current_state["consolidated_data"] = consolidated
        self.current_state["skip_optional"] = skip_optional

        # Clear missing fields that were provided
        provided_keys = set(user_data.keys())
        self.current_state["missing_critical"] = [
            field for field in self.current_state.get("missing_critical", [])
            if field not in provided_keys
        ]
        self.current_state["missing_optional"] = [
            field for field in self.current_state.get("missing_optional", [])
            if field not in provided_keys
        ]

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"✅ Données ajoutées avec succès:\n" +
                           "\n".join([f"- {k}: {v}" for k, v in user_data.items()])
                }
            ]
        }

    async def generate_pdf(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Generate the final PDF"""

        if not self.current_state:
            raise ValueError("No active session. Please extract documents first.")

        format_type = arguments.get("format", "base64")

        # Run PDF generation
        try:
            result = await self.graph.ainvoke(self.current_state)

            if not result.get("generated_pdf"):
                raise ValueError("Failed to generate PDF")

            pdf_bytes = result["generated_pdf"]

            if format_type == "base64":
                # Return base64 encoded PDF
                pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')

                return {
                    "content": [
                        {
                            "type": "text",
                            "text": "✅ PDF généré avec succès"
                        },
                        {
                            "type": "resource",
                            "resource": {
                                "uri": f"data:application/pdf;base64,{pdf_base64}",
                                "mimeType": "application/pdf",
                                "name": f"form_3916_{self.session_id}.pdf"
                            }
                        }
                    ]
                }
            else:
                # Save to file and return path
                output_dir = Path(__file__).parent.parent / "packs" / "form_3916" / "pdf_filled"
                output_dir.mkdir(exist_ok=True)

                output_path = output_dir / f"form_3916_{self.session_id}.pdf"
                with open(output_path, "wb") as f:
                    f.write(pdf_bytes)

                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"✅ PDF sauvegardé: {output_path}"
                        }
                    ]
                }

        except Exception as e:
            logger.error(f"PDF generation error: {e}")
            raise

    def get_status(self) -> Dict[str, Any]:
        """Get current processing status"""

        if not self.current_state:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "❌ Aucune session active"
                    }
                ]
            }

        status = []
        status.append(f"📊 Session: {self.session_id}")

        # Extracted data
        consolidated = self.current_state.get("consolidated_data", {})
        if consolidated:
            status.append("\n✅ Données extraites/fournies:")
            for key, value in consolidated.items():
                if not key.startswith("_") and value:
                    status.append(f"  • {key}: {value}")

        # Missing fields
        missing_critical = self.current_state.get("missing_critical", [])
        missing_optional = self.current_state.get("missing_optional", [])

        if missing_critical:
            status.append(f"\n⚠️ Champs critiques manquants: {', '.join(missing_critical)}")

        if missing_optional:
            status.append(f"\n📝 Champs optionnels manquants: {', '.join(missing_optional)}")

        # PDF status
        if self.current_state.get("generated_pdf"):
            status.append("\n✅ PDF généré et prêt")
        else:
            status.append("\n⏳ PDF non encore généré")

        return {
            "content": [
                {
                    "type": "text",
                    "text": "\n".join(status)
                }
            ]
        }

    def list_resources(self) -> Dict[str, Any]:
        """List available resources"""

        resources = []

        if self.current_state:
            resources.append({
                "uri": f"form3916://session/{self.session_id}/state",
                "name": "Current Form State",
                "description": "Current state of the form processing",
                "mimeType": "application/json"
            })

            if self.current_state.get("generated_pdf"):
                resources.append({
                    "uri": f"form3916://session/{self.session_id}/pdf",
                    "name": "Generated PDF",
                    "description": "The generated Form 3916 PDF",
                    "mimeType": "application/pdf"
                })

        return {"resources": resources}

    async def read_resource(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Read a resource"""

        uri = params.get("uri", "")

        if "/state" in uri:
            # Return current state as JSON
            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps(self._get_serializable_state(), indent=2)
                    }
                ]
            }
        elif "/pdf" in uri:
            # Return PDF as base64
            if self.current_state and self.current_state.get("generated_pdf"):
                pdf_base64 = base64.b64encode(
                    self.current_state["generated_pdf"]
                ).decode('utf-8')

                return {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "application/pdf",
                            "blob": pdf_base64
                        }
                    ]
                }

        raise ValueError(f"Resource not found: {uri}")

    def _format_extraction_result(self, result: Dict[str, Any]) -> str:
        """Format extraction result for display"""

        lines = ["📄 Extraction terminée\n"]

        # Classified documents
        classified = result.get("classified_docs", [])
        if classified:
            lines.append("📁 Documents classifiés:")
            for doc in classified:
                lines.append(f"  • {doc.get('filename', doc.get('file_name', 'Unknown'))}: {doc['doc_type']}")

        # Extracted data
        consolidated = result.get("consolidated_data", {})
        if consolidated:
            lines.append("\n✅ Données extraites:")
            for key, value in consolidated.items():
                if not key.startswith("_") and value:
                    lines.append(f"  • {key}: {value}")

        # Missing fields
        missing_critical = result.get("missing_critical", [])
        missing_optional = result.get("missing_optional", [])

        if missing_critical:
            lines.append(f"\n⚠️ Champs critiques manquants:")
            for field in missing_critical:
                lines.append(f"  • {field}")

        if missing_optional:
            lines.append(f"\n📝 Champs optionnels manquants:")
            for field in missing_optional:
                lines.append(f"  • {field}")

        return "\n".join(lines)

    def _get_serializable_state(self) -> Dict[str, Any]:
        """Get state in serializable format"""

        if not self.current_state:
            return {}

        # Create a copy without binary data
        state = self.current_state.copy()

        # Remove binary fields
        state.pop("input_files", None)
        state.pop("generated_pdf", None)

        # Convert Pydantic models to dicts
        if "extracted_data_list" in state:
            state["extracted_data_list"] = [
                data.model_dump() if hasattr(data, "model_dump") else data
                for data in state["extracted_data_list"]
            ]

        return state


async def run_server():
    """Run the MCP server"""

    server = Form3916MCPServer()

    logger.info("Form 3916 MCP Server started")
    logger.info("Listening for JSON-RPC requests on stdin...")

    # Read from stdin and write to stdout (MCP protocol)
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break

            # Skip empty lines
            line = line.strip()
            if not line:
                continue

            # Parse JSON-RPC request
            request = json.loads(line)

            # Handle request
            response = await server.handle_request(request)

            # Send response
            print(json.dumps(response))
            sys.stdout.flush()

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {e}")
        except Exception as e:
            logger.error(f"Server error: {e}")
            # Send error response with a default id
            error_response = {
                "jsonrpc": "2.0",
                "id": 0,  # Default id for error cases
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
            print(json.dumps(error_response))
            sys.stdout.flush()


if __name__ == "__main__":
    # Run the server
    asyncio.run(run_server())