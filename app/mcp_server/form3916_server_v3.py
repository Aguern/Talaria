#!/usr/bin/env python3
"""
MCP Server for Form 3916 - Version 3
Robust JSON serialization and state management
"""

import asyncio
import json
import logging
import sys
import base64
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

# Configure logging to stderr to not interfere with stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)


class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles Pydantic models and Enums"""

    def default(self, obj):
        # Handle Pydantic models
        if hasattr(obj, 'model_dump'):
            return obj.model_dump()
        elif hasattr(obj, 'dict'):
            return obj.dict()
        # Handle Enums
        elif isinstance(obj, Enum):
            return obj.value
        # Handle bytes
        elif isinstance(obj, bytes):
            return base64.b64encode(obj).decode('utf-8')
        # Default
        return super().default(obj)


def deep_clean_for_json(obj):
    """Recursively clean an object for JSON serialization"""

    if obj is None:
        return None
    elif isinstance(obj, (str, int, float, bool)):
        return obj
    elif isinstance(obj, bytes):
        return None  # Don't include binary data in cleaned version
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

    # Class-level storage to persist between method calls in the same process
    _sessions: Dict[str, Dict[str, Any]] = {}
    _current_session_id: Optional[str] = None

    def __init__(self):
        self.graph = None
        self.encoder = JSONEncoder()

    @property
    def current_state(self):
        """Get current state from class-level storage"""
        if self._current_session_id and self._current_session_id in self._sessions:
            return self._sessions[self._current_session_id]
        return None

    @current_state.setter
    def current_state(self, value):
        """Set current state in class-level storage"""
        if not self._current_session_id:
            self._current_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._sessions[self._current_session_id] = value

    @property
    def session_id(self):
        """Get current session ID"""
        return self._current_session_id

    @session_id.setter
    def session_id(self, value):
        """Set current session ID"""
        self._current_session_id = value

    def _serialize_state(self, state: Dict[str, Any]) -> str:
        """Serialize state to JSON string"""
        try:
            return json.dumps(state, cls=JSONEncoder)
        except Exception as e:
            logger.error(f"Serialization error: {e}")
            # Fallback to deep cleaning
            cleaned = deep_clean_for_json(state)
            return json.dumps(cleaned)

    def _clean_state_for_storage(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Clean state for internal storage and graph invocation"""

        if not state:
            return {}

        cleaned = {}

        for key, value in state.items():
            if key == "extracted_data_list":
                # Convert Pydantic models to dicts
                cleaned[key] = []
                for item in value:
                    if hasattr(item, 'model_dump'):
                        cleaned[key].append(item.model_dump())
                    elif isinstance(item, dict):
                        cleaned[key].append(item)
                    else:
                        cleaned[key].append(deep_clean_for_json(item))

            elif key == "classified_docs":
                # Convert doc classification results
                cleaned[key] = []
                for doc in value:
                    clean_doc = {}
                    for doc_key, doc_val in doc.items():
                        if isinstance(doc_val, Enum):
                            clean_doc[doc_key] = doc_val.value
                        else:
                            clean_doc[doc_key] = str(doc_val)
                    cleaned[key].append(clean_doc)

            elif key in ["input_files", "generated_pdf"]:
                # Keep binary data as is for processing
                cleaned[key] = value

            elif key == "pdf_data":
                # Clean PDF data if it exists
                if value:
                    cleaned[key] = deep_clean_for_json(value)
                else:
                    cleaned[key] = None

            else:
                # Clean other fields
                cleaned[key] = deep_clean_for_json(value)

        return cleaned

    async def run(self):
        """Main server loop - reads JSON-RPC from stdin, writes to stdout"""
        logger.info("Form 3916 MCP Server v3 starting...")

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

        # If no id provided, use a default value
        if request_id is None:
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
                "version": "3.0.0"
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
                            "description": "User data to complete the form"
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
            },
            {
                "name": "form3916_direct",
                "description": "Generate Form 3916 directly from complete data without document extraction",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "declarant": {
                            "type": "object",
                            "description": "Declarant information",
                            "properties": {
                                "nom": {"type": "string"},
                                "prenom": {"type": "string"},
                                "date_naissance": {"type": "string"},
                                "lieu_naissance": {"type": "string"},
                                "adresse": {"type": "string"},
                                "code_postal": {"type": "string"},
                                "ville": {"type": "string"},
                                "pays": {"type": "string"}
                            }
                        },
                        "compte": {
                            "type": "object",
                            "description": "Account information",
                            "properties": {
                                "numero_compte": {"type": "string"},
                                "designation_etablissement": {"type": "string"},
                                "adresse_etablissement": {"type": "string"},
                                "date_ouverture": {"type": "string"},
                                "date_cloture": {"type": "string"},
                                "qualite_declarant": {"type": "string"},
                                "usage": {"type": "string"},
                                "pays": {"type": "string"}
                            }
                        },
                        "annee_declaration": {
                            "type": "string",
                            "description": "Year of declaration"
                        }
                    },
                    "required": ["declarant", "compte"]
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
        elif tool_name == "form3916_direct":
            return await self.generate_direct(arguments)
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

        # Run extraction workflow
        try:
            logger.info("Starting extraction workflow...")
            result = await self.graph.ainvoke(initial_state)

            # Clean and store the state
            self.current_state = self._clean_state_for_storage(result)

            # Format result
            lines = ["📄 Extraction terminée\n"]

            # Extracted data
            consolidated = self.current_state.get("consolidated_data", {})
            if consolidated:
                lines.append("✅ Données extraites:")
                for key, value in consolidated.items():
                    if not key.startswith("_") and value:
                        lines.append(f"  • {key}: {value}")

            # Missing fields
            missing_critical = self.current_state.get("missing_critical", [])
            missing_optional = self.current_state.get("missing_optional", [])

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
            logger.error(f"Extraction error: {e}", exc_info=True)
            raise

    async def complete_with_user_data(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Complete form with user-provided data"""

        user_data = arguments.get("user_data", {})
        skip_optional = arguments.get("skip_optional", False)

        # If no current state, initialize one
        if not self.current_state:
            logger.info("No active session, creating one from user data")
            self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.current_state = {
                "input_files": [],
                "user_context": "",
                "classified_docs": [],
                "extracted_data_list": [],
                "consolidated_data": {},
                "missing_critical": [],
                "missing_optional": [],
                "skip_optional": skip_optional,
                "pdf_data": None,
                "generated_pdf": None
            }

        logger.info(f"Adding user data: {user_data}")

        # Handle nested structure if provided
        if "declarant" in user_data and "compte" in user_data:
            # Transform nested structure to flat structure
            declarant = user_data.get("declarant", {})
            compte = user_data.get("compte", {})

            flat_data = {
                # Declarant info
                "nom": declarant.get("nom"),
                "prenom": declarant.get("prenom"),
                "date_naissance": declarant.get("date_naissance"),
                "lieu_naissance": declarant.get("lieu_naissance"),
                "adresse_complete": f"{declarant.get('adresse', '')}, {declarant.get('code_postal', '')} {declarant.get('ville', '')}, {declarant.get('pays', '')}".strip(),

                # Account info
                "numero_compte": compte.get("numero_compte"),
                "designation_etablissement": compte.get("designation_etablissement"),
                "adresse_etablissement": compte.get("adresse_etablissement"),
                "date_ouverture": compte.get("date_ouverture"),
                "date_cloture": compte.get("date_cloture"),
                "nature_compte": "COMPTE_BANCAIRE",
                "type_compte": "COURANT",
                "modalite_detention": compte.get("qualite_declarant", "TITULAIRE"),
                "usage_compte": compte.get("usage", "PERSONNEL"),

                # Signature
                "lieu_signature": declarant.get("ville", ""),
                "date_signature": datetime.now().strftime("%d/%m/%Y")
            }

            # Remove None values
            user_data = {k: v for k, v in flat_data.items() if v is not None}

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

        # If we have all required fields, clear the missing lists
        required_fields = ["nom", "prenom", "numero_compte", "designation_etablissement"]
        if all(field in consolidated for field in required_fields):
            self.current_state["missing_critical"] = []
            # Mark optional fields as skip if we have the main data
            self.current_state["skip_optional"] = True

        logger.info(f"Consolidated data after: {consolidated}")
        logger.info(f"State ready for PDF: {len(consolidated)} fields")

        # Better response formatting
        response_text = "✅ Données ajoutées avec succès\n\n"
        response_text += f"📊 {len(consolidated)} champs remplis\n"

        if self.current_state.get("missing_critical"):
            response_text += f"⚠️ Champs manquants: {', '.join(self.current_state['missing_critical'])}\n"
        else:
            response_text += "✅ Toutes les données requises sont présentes\n"
            response_text += "👉 Utilisez form3916_generate pour créer le PDF"

        return {
            "content": [
                {
                    "type": "text",
                    "text": response_text
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
            logger.info(f"Generating PDF with consolidated data: {self.current_state.get('consolidated_data', {})}")

            # Invoke graph with cleaned state
            result = await self.graph.ainvoke(self.current_state)

            # Update state with result
            self.current_state = self._clean_state_for_storage(result)

            if not result.get("generated_pdf"):
                logger.error(f"No PDF in result. Missing fields: {result.get('missing_critical', [])}")
                raise ValueError(f"Failed to generate PDF. Missing critical fields: {result.get('missing_critical', [])}")

            pdf_bytes = result["generated_pdf"]
            logger.info(f"PDF generated successfully: {len(pdf_bytes)} bytes")

            if format_type == "base64":
                # Return base64 encoded PDF
                try:
                    pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')

                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": f"✅ PDF généré avec succès ({len(pdf_bytes)} octets)"
                            }
                        ],
                        "isError": False
                    }

                except Exception as e:
                    logger.error(f"Base64 encoding error: {e}")
                    # Fallback to file
                    format_type = "file"

            if format_type == "file":
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
                            "text": f"✅ PDF sauvegardé: {output_path}\n📊 Taille: {len(pdf_bytes)} octets"
                        }
                    ]
                }

        except Exception as e:
            logger.error(f"PDF generation error: {e}", exc_info=True)
            raise

    async def generate_direct(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Form 3916 directly from complete data"""

        logger.info("Direct generation from complete data")

        # First, set the complete data using complete_with_user_data
        complete_result = await self.complete_with_user_data({
            "user_data": arguments,
            "skip_optional": True
        })

        # Then generate the PDF
        generate_result = await self.generate_pdf({
            "format": "file"  # Use file to avoid base64 issues
        })

        return generate_result

    def get_status(self) -> Dict[str, Any]:
        """Get current processing status"""

        if not self.current_state:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "❌ Aucune session active. Utilisez form3916_extract d'abord."
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

        return {"resources": resources}

    async def handle_resource_read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Read a resource"""

        uri = params.get("uri", "")

        if "/state" in uri:
            # Return current state as JSON (remove binary data)
            state_for_display = deep_clean_for_json(self.current_state) if self.current_state else {}

            # Remove large binary fields
            state_for_display.pop("input_files", None)
            state_for_display.pop("generated_pdf", None)

            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps(state_for_display, indent=2)
                    }
                ]
            }

        raise ValueError(f"Resource not found: {uri}")

    def handle_prompts_list(self) -> Dict[str, Any]:
        """List available prompts"""

        prompts = [
            {
                "name": "form3916_workflow",
                "description": "Complete workflow for Form 3916 processing"
            }
        ]

        return {"prompts": prompts}

    def handle_prompt_get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get a specific prompt"""

        name = params.get("name")

        if name == "form3916_workflow":
            return {
                "messages": [
                    {
                        "role": "user",
                        "content": "J'ai besoin d'aide pour remplir le formulaire 3916."
                    },
                    {
                        "role": "assistant",
                        "content": """Je vais vous aider à remplir le formulaire 3916 pour déclarer vos comptes à l'étranger.

Voici les étapes :
1. J'analyserai vos documents (relevés bancaires, CNI, etc.)
2. J'extrairai automatiquement les informations
3. Je vous demanderai les données manquantes
4. Je générerai le PDF complété

Veuillez fournir vos documents pour commencer."""
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