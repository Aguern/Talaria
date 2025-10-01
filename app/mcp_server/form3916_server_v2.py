#!/usr/bin/env python3
"""
MCP Server for Form 3916 - Version 2
Using proper MCP protocol implementation
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

# Configure logging to stderr to not interfere with stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)


class Form3916MCPServer:
    """MCP Server for Form 3916 processing"""

    def __init__(self):
        self.graph = None
        self.current_state: Optional[Dict[str, Any]] = None
        self.session_id = None

    def _clean_state_for_json(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Clean state to make it JSON-serializable"""
        clean = state.copy()

        # Convert Pydantic models in extracted_data_list
        if "extracted_data_list" in clean:
            clean["extracted_data_list"] = [
                data.model_dump() if hasattr(data, "model_dump") else data
                for data in clean["extracted_data_list"]
            ]

        # Convert Enums in classified_docs
        if "classified_docs" in clean:
            clean["classified_docs"] = [
                {
                    "filename": doc.get("filename", ""),
                    "doc_type": str(doc.get("doc_type", ""))
                }
                for doc in clean["classified_docs"]
            ]

        # Remove binary data for display/storage
        clean.pop("input_files", None)
        clean.pop("generated_pdf", None)

        return clean

    async def run(self):
        """Main server loop - reads JSON-RPC from stdin, writes to stdout"""
        logger.info("Form 3916 MCP Server starting...")

        while True:
            try:
                line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                if not line:
                    break

                line = line.strip()
                if not line:
                    continue

                try:
                    request = json.loads(line)
                    response = await self.handle_request(request)

                    # Only write response if not None
                    if response is not None:
                        print(json.dumps(response), flush=True)

                except json.JSONDecodeError as e:
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32700,
                            "message": f"Parse error: {str(e)}"
                        }
                    }
                    print(json.dumps(error_response), flush=True)

            except KeyboardInterrupt:
                logger.info("Server shutdown requested")
                break
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                continue

    async def handle_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle JSON-RPC request"""

        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        # If no id provided, use a default value (Claude Desktop seems to need this)
        if request_id is None:
            # For notifications, we still need to respond with an id
            request_id = 0

        logger.debug(f"Handling request: {method} (id={request_id})")

        try:
            # Route to appropriate handler
            if method == "initialize":
                result = self.handle_initialize(params)
            elif method == "initialized":
                # This is a notification, just acknowledge
                result = {}
            elif method == "tools/list":
                result = self.handle_tools_list()
            elif method == "tools/call":
                result = await self.handle_tool_call(params)
            elif method == "resources/list":
                result = self.handle_resources_list()
            elif method == "resources/read":
                result = await self.handle_resource_read(params)
            elif method == "prompts/list":
                result = self.handle_prompts_list()
            elif method == "prompts/get":
                result = self.handle_prompt_get(params)
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }

            # Always return a proper response with an id
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }

        except Exception as e:
            logger.error(f"Error handling {method}: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }

    def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialize request"""

        # Initialize the graph here
        self.graph = create_modern_form3916_graph(use_checkpointer=False)
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
                "resources": {},
                "prompts": {}
            },
            "serverInfo": {
                "name": "form3916",
                "version": "2.0.0"
            }
        }

    def handle_tools_list(self) -> Dict[str, Any]:
        """List available tools"""

        tools = [
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
                                    "name": {
                                        "type": "string",
                                        "description": "File name"
                                    },
                                    "content": {
                                        "type": "string",
                                        "description": "Base64 encoded content"
                                    }
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
                                "date_naissance": {
                                    "type": "string",
                                    "description": "Date of birth (DD/MM/YYYY)"
                                },
                                "lieu_naissance": {
                                    "type": "string",
                                    "description": "Place of birth"
                                },
                                "adresse_complete": {
                                    "type": "string",
                                    "description": "Complete address"
                                },
                                "lieu_signature": {
                                    "type": "string",
                                    "description": "Place of signature"
                                },
                                "date_cloture": {
                                    "type": "string",
                                    "description": "Account closure date (optional)"
                                }
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
                            "enum": ["base64", "file"],
                            "description": "Output format for the PDF",
                            "default": "base64"
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

        return {"tools": tools}

    async def handle_tool_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool call"""

        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        logger.info(f"Tool call: {tool_name}")

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

            # Clean state for storage
            self.current_state = self._clean_state_for_json(result)
            # But keep the binary data in the original result
            self.current_state["input_files"] = result.get("input_files", [])
            self.current_state["generated_pdf"] = result.get("generated_pdf")

            # Format result
            lines = ["📄 Extraction terminée\n"]

            # Extracted data
            consolidated = result.get("consolidated_data", {})
            if consolidated:
                lines.append("✅ Données extraites:")
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

            return {
                "content": [
                    {
                        "type": "text",
                        "text": "\n".join(lines)
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

        # Log for debugging
        logger.info(f"Adding user data: {user_data}")
        logger.info(f"Current consolidated data before: {self.current_state.get('consolidated_data', {})}")

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

        logger.info(f"Consolidated data after: {self.current_state.get('consolidated_data', {})}")

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
            # Log current state for debugging
            logger.info(f"Generating PDF with state keys: {list(self.current_state.keys())}")
            logger.info(f"Consolidated data: {self.current_state.get('consolidated_data', {})}")

            # The state is already cleaned, just invoke
            result = await self.graph.ainvoke(self.current_state)

            if not result.get("generated_pdf"):
                logger.error(f"No PDF in result. Keys: {list(result.keys())}")
                logger.error(f"Missing fields: critical={result.get('missing_critical')}, optional={result.get('missing_optional')}")
                raise ValueError(f"Failed to generate PDF. Missing critical fields: {result.get('missing_critical', [])}")

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

    def handle_resources_list(self) -> Dict[str, Any]:
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

    async def handle_resource_read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Read a resource"""

        uri = params.get("uri", "")

        if "/state" in uri:
            # Return current state as JSON (already cleaned)
            state_copy = self._clean_state_for_json(self.current_state) if self.current_state else {}

            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps(state_copy, indent=2)
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

    def handle_prompts_list(self) -> Dict[str, Any]:
        """List available prompts"""

        prompts = [
            {
                "name": "form3916_workflow",
                "description": "Complete workflow for Form 3916 processing",
                "arguments": [
                    {
                        "name": "has_documents",
                        "description": "Whether the user has documents to upload",
                        "required": False
                    }
                ]
            }
        ]

        return {"prompts": prompts}

    def handle_prompt_get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get a specific prompt"""

        name = params.get("name")
        arguments = params.get("arguments", {})

        if name == "form3916_workflow":
            has_docs = arguments.get("has_documents", True)

            if has_docs:
                prompt_text = """Je vais vous aider à remplir le formulaire 3916 pour déclarer vos comptes à l'étranger.

1. D'abord, je vais analyser vos documents (relevés bancaires, CNI, etc.)
2. J'extrairai automatiquement les informations
3. Je vous demanderai les données manquantes
4. Je générerai le PDF complété

Veuillez fournir vos documents."""
            else:
                prompt_text = """Je vais vous aider à remplir le formulaire 3916.

Comme vous n'avez pas de documents, j'aurai besoin des informations suivantes :
- Vos nom et prénom
- Date et lieu de naissance
- Adresse complète
- Informations sur le compte (banque, IBAN, date d'ouverture)

Commençons par vos informations personnelles."""

            return {
                "description": "Guide for Form 3916 completion",
                "messages": [
                    {
                        "role": "user",
                        "content": f"J'ai besoin d'aide pour remplir le formulaire 3916."
                    },
                    {
                        "role": "assistant",
                        "content": prompt_text
                    }
                ]
            }

        raise ValueError(f"Unknown prompt: {name}")


async def main():
    """Main entry point"""
    server = Form3916MCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())