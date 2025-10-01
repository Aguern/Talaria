#!/usr/bin/env python3
"""
MCP Server for Form 3916 - Version 4
With proper session persistence for the complete workflow
"""

import asyncio
import json
import logging
import sys
import base64
import pickle
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.packs.form_3916.graph_modern import (
    create_modern_form3916_graph,
    Form3916StateModern
)

# Configure logging to stderr
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)

# Session storage file
SESSION_FILE = Path("/tmp/mcp_form3916_session.pkl")


def deep_clean_for_json(obj):
    """Recursively clean an object for JSON serialization"""
    if obj is None:
        return None
    elif isinstance(obj, (str, int, float, bool)):
        return obj
    elif isinstance(obj, bytes):
        return None  # Don't include binary data
    elif hasattr(obj, 'model_dump'):
        return obj.model_dump()
    elif hasattr(obj, 'dict'):
        return obj.dict()
    elif isinstance(obj, Enum):
        return obj.value
    elif isinstance(obj, dict):
        return {k: deep_clean_for_json(v) for k, v in obj.items() if v is not None}
    elif isinstance(obj, (list, tuple)):
        return [deep_clean_for_json(item) for item in obj]
    else:
        return str(obj)


class Form3916MCPServer:
    """MCP Server for Form 3916 processing"""

    def __init__(self):
        self.graph = None
        # Load existing session if available
        self.load_session()

    def load_session(self):
        """Load session from disk"""
        if SESSION_FILE.exists():
            try:
                with open(SESSION_FILE, 'rb') as f:
                    data = pickle.load(f)
                    self.current_state = data.get('state')
                    self.session_id = data.get('session_id')
                    logger.info(f"Loaded existing session: {self.session_id}")
            except Exception as e:
                logger.error(f"Failed to load session: {e}")
                self.current_state = None
                self.session_id = None
        else:
            self.current_state = None
            self.session_id = None

    def save_session(self):
        """Save session to disk"""
        try:
            with open(SESSION_FILE, 'wb') as f:
                pickle.dump({
                    'state': self.current_state,
                    'session_id': self.session_id
                }, f)
            logger.info(f"Saved session: {self.session_id}")
        except Exception as e:
            logger.error(f"Failed to save session: {e}")

    def clear_session(self):
        """Clear the current session"""
        self.current_state = None
        self.session_id = None
        if SESSION_FILE.exists():
            SESSION_FILE.unlink()
        logger.info("Session cleared")

    async def run(self):
        """Main server loop"""
        logger.info("Form 3916 MCP Server v4 starting...")

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
        request_id = request.get("id", 0)

        logger.debug(f"Handling: {method} (session={self.session_id})")

        try:
            if method == "initialize":
                result = self.handle_initialize(params)
            elif method == "initialized":
                result = {}
            elif method == "tools/list":
                result = self.handle_tools_list()
            elif method == "tools/call":
                result = await self.handle_tool_call(params)
            elif method == "resources/list":
                result = self.handle_resources_list()
            elif method == "resources/read":
                result = await self.handle_resource_read(params)
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }

            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }

        except Exception as e:
            logger.error(f"Error handling {method}: {e}", exc_info=True)
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

        self.graph = create_modern_form3916_graph(use_checkpointer=False)

        # Don't clear session on initialize - keep existing if available
        if not self.session_id:
            self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
                "resources": {}
            },
            "serverInfo": {
                "name": "form3916",
                "version": "4.0.0"
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
                                    "name": {"type": "string"},
                                    "content": {"type": "string"}
                                },
                                "required": ["name", "content"]
                            }
                        },
                        "user_context": {
                            "type": "string",
                            "description": "Additional context"
                        }
                    },
                    "required": ["documents"]
                }
            },
            {
                "name": "form3916_complete",
                "description": "Complete missing fields with user data",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "user_data": {
                            "type": "object",
                            "description": "Additional user data"
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
                            "default": "file"
                        }
                    }
                }
            },
            {
                "name": "form3916_status",
                "description": "Get current session status",
                "inputSchema": {
                    "type": "object"
                }
            },
            {
                "name": "form3916_clear",
                "description": "Clear current session and start fresh",
                "inputSchema": {
                    "type": "object"
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
        elif tool_name == "form3916_clear":
            return self.clear_and_restart()
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    async def extract_from_documents(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data from documents"""

        # Clear any existing session for new extraction
        self.clear_session()
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        documents = arguments.get("documents", [])
        user_context = arguments.get("user_context", "")

        # Decode documents
        input_files = []
        for doc in documents:
            name = doc["name"]
            content = base64.b64decode(doc["content"])
            input_files.append({name: content})

        # Initial state
        initial_state = {
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

        try:
            logger.info("Starting extraction workflow...")

            if not self.graph:
                self.graph = create_modern_form3916_graph(use_checkpointer=False)

            result = await self.graph.ainvoke(initial_state)

            # Clean state for storage
            self.current_state = self._clean_state_for_storage(result)
            self.save_session()

            # Format response
            lines = ["📄 Extraction terminée\n"]

            # Show classified documents
            classified = self.current_state.get("classified_docs", [])
            if classified:
                lines.append("📁 Documents analysés:")
                for doc in classified:
                    doc_name = doc.get("filename", "Document")
                    doc_type = doc.get("doc_type", "INCONNU")
                    lines.append(f"  • {doc_name}: {doc_type}")

            # Show extracted data
            consolidated = self.current_state.get("consolidated_data", {})
            if consolidated:
                lines.append("\n✅ Données extraites:")
                for key, value in consolidated.items():
                    if not key.startswith("_") and value:
                        lines.append(f"  • {key}: {value}")

            # Show missing fields
            missing_critical = self.current_state.get("missing_critical", [])
            missing_optional = self.current_state.get("missing_optional", [])

            if missing_critical:
                lines.append(f"\n⚠️ Données critiques manquantes:")
                for field in missing_critical:
                    lines.append(f"  • {field}")
                lines.append("\n👉 Utilisez form3916_complete pour ajouter ces données")

            elif missing_optional:
                lines.append(f"\n📝 Données optionnelles manquantes:")
                for field in missing_optional:
                    lines.append(f"  • {field}")
                lines.append("\n👉 Utilisez form3916_complete ou form3916_generate directement")

            else:
                lines.append("\n✅ Toutes les données sont complètes")
                lines.append("👉 Utilisez form3916_generate pour créer le PDF")

            return {
                "content": [
                    {
                        "type": "text",
                        "text": "\n".join(lines)
                    }
                ]
            }

        except Exception as e:
            logger.error(f"Extraction error: {e}", exc_info=True)
            raise

    async def complete_with_user_data(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Complete with user data"""

        if not self.current_state:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "❌ Aucune session active.\n👉 Utilisez d'abord form3916_extract avec vos documents"
                    }
                ]
            }

        user_data = arguments.get("user_data", {})

        # Update consolidated data
        consolidated = self.current_state.get("consolidated_data", {})
        consolidated.update(user_data)
        self.current_state["consolidated_data"] = consolidated

        # Update missing fields
        provided_keys = set(user_data.keys())
        self.current_state["missing_critical"] = [
            f for f in self.current_state.get("missing_critical", [])
            if f not in provided_keys
        ]
        self.current_state["missing_optional"] = [
            f for f in self.current_state.get("missing_optional", [])
            if f not in provided_keys
        ]

        # Save session
        self.save_session()

        # Format response
        lines = ["✅ Données ajoutées avec succès:\n"]
        for key, value in user_data.items():
            lines.append(f"  • {key}: {value}")

        if self.current_state.get("missing_critical"):
            lines.append(f"\n⚠️ Encore manquant: {', '.join(self.current_state['missing_critical'])}")
        else:
            lines.append("\n✅ Toutes les données requises sont présentes")
            lines.append("👉 Utilisez form3916_generate pour créer le PDF")

        return {
            "content": [
                {
                    "type": "text",
                    "text": "\n".join(lines)
                }
            ]
        }

    async def generate_pdf(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Generate PDF"""

        if not self.current_state:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "❌ Aucune session active.\n👉 Utilisez d'abord form3916_extract avec vos documents"
                    }
                ]
            }

        format_type = arguments.get("format", "file")

        try:
            logger.info(f"Generating PDF with {len(self.current_state.get('consolidated_data', {}))} fields")

            if not self.graph:
                self.graph = create_modern_form3916_graph(use_checkpointer=False)

            # Skip optional fields and generate
            self.current_state["skip_optional"] = True
            result = await self.graph.ainvoke(self.current_state)

            if not result.get("generated_pdf"):
                missing = result.get("missing_critical", [])
                raise ValueError(f"Impossible de générer le PDF. Champs manquants: {missing}")

            pdf_bytes = result["generated_pdf"]
            logger.info(f"PDF generated: {len(pdf_bytes)} bytes")

            # Save PDF
            output_dir = Path(__file__).parent.parent / "packs" / "form_3916" / "pdf_filled"
            output_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = output_dir / f"form_3916_{timestamp}.pdf"

            with open(output_path, "wb") as f:
                f.write(pdf_bytes)

            # Clear session after successful generation
            self.clear_session()

            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"✅ PDF généré avec succès!\n📄 Fichier: {output_path}\n📊 Taille: {len(pdf_bytes):,} octets"
                    }
                ]
            }

        except Exception as e:
            logger.error(f"PDF generation error: {e}", exc_info=True)
            raise

    def get_status(self) -> Dict[str, Any]:
        """Get session status"""

        if not self.current_state:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "❌ Aucune session active\n👉 Utilisez form3916_extract pour commencer"
                    }
                ]
            }

        lines = [f"📊 Session active: {self.session_id}\n"]

        # Show data
        consolidated = self.current_state.get("consolidated_data", {})
        if consolidated:
            lines.append("✅ Données disponibles:")
            for key, value in list(consolidated.items())[:10]:  # Show first 10
                if not key.startswith("_") and value:
                    lines.append(f"  • {key}: {value}")

        # Show missing
        missing_critical = self.current_state.get("missing_critical", [])
        missing_optional = self.current_state.get("missing_optional", [])

        if missing_critical:
            lines.append(f"\n⚠️ Manquant (critique): {', '.join(missing_critical)}")
        if missing_optional:
            lines.append(f"\n📝 Manquant (optionnel): {', '.join(missing_optional)}")

        if not missing_critical:
            lines.append("\n✅ Prêt pour génération PDF")

        return {
            "content": [
                {
                    "type": "text",
                    "text": "\n".join(lines)
                }
            ]
        }

    def clear_and_restart(self) -> Dict[str, Any]:
        """Clear session and start fresh"""

        self.clear_session()

        return {
            "content": [
                {
                    "type": "text",
                    "text": "🔄 Session effacée\n👉 Utilisez form3916_extract pour commencer une nouvelle session"
                }
            ]
        }

    def _clean_state_for_storage(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Clean state for storage"""

        if not state:
            return {}

        cleaned = {}

        for key, value in state.items():
            if key == "extracted_data_list":
                cleaned[key] = [
                    item.model_dump() if hasattr(item, 'model_dump') else item
                    for item in value
                ]
            elif key == "classified_docs":
                cleaned[key] = [
                    {
                        "filename": doc.get("filename", ""),
                        "doc_type": str(doc.get("doc_type", ""))
                    }
                    for doc in value
                ]
            elif key in ["input_files", "generated_pdf"]:
                cleaned[key] = value  # Keep binary
            else:
                cleaned[key] = deep_clean_for_json(value)

        return cleaned

    def handle_resources_list(self) -> Dict[str, Any]:
        """List resources"""

        resources = []
        if self.current_state:
            resources.append({
                "uri": f"form3916://session/{self.session_id}",
                "name": "Current Session",
                "mimeType": "application/json"
            })

        return {"resources": resources}

    async def handle_resource_read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Read resource"""

        if not self.current_state:
            raise ValueError("No active session")

        # Return session state without binary data
        display_state = deep_clean_for_json(self.current_state)
        display_state.pop("input_files", None)
        display_state.pop("generated_pdf", None)

        return {
            "contents": [
                {
                    "uri": params.get("uri", ""),
                    "mimeType": "application/json",
                    "text": json.dumps(display_state, indent=2)
                }
            ]
        }


async def main():
    """Main entry point"""
    server = Form3916MCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())