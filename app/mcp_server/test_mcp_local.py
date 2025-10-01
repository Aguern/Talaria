#!/usr/bin/env python3
"""
Test script for Form 3916 MCP Server
Tests locally without Claude Desktop
"""

import asyncio
import json
import base64
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent.parent))

from app.mcp_server.form3916_server import Form3916MCPServer


async def test_mcp_server():
    """Test the MCP server with sample data"""

    print("=" * 70)
    print("TEST DU SERVEUR MCP FORM 3916")
    print("=" * 70)

    server = Form3916MCPServer()

    # 1. Initialize
    print("\n1️⃣ Initialisation...")
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {}
    }
    response = await server.handle_request(init_request)
    print(f"✅ Serveur initialisé: {response['result']['serverInfo']}")

    # 2. List tools
    print("\n2️⃣ Liste des outils disponibles...")
    tools_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    response = await server.handle_request(tools_request)
    tools = response['result']['tools']
    print(f"✅ {len(tools)} outils disponibles:")
    for tool in tools:
        print(f"   - {tool['name']}: {tool['description']}")

    # 3. Load test documents
    print("\n3️⃣ Chargement des documents de test...")
    docs_path = Path(__file__).parent.parent / "packs" / "form_3916"
    documents = []

    revolut_path = docs_path / "Revolut.txt"
    if revolut_path.exists():
        with open(revolut_path, 'rb') as f:
            content = base64.b64encode(f.read()).decode('utf-8')
            documents.append({
                "name": "Revolut.txt",
                "content": content
            })
        print("  ✅ Revolut.txt chargé")

    cni_path = docs_path / "CNI.pdf"
    if cni_path.exists():
        with open(cni_path, 'rb') as f:
            content = base64.b64encode(f.read()).decode('utf-8')
            documents.append({
                "name": "CNI.pdf",
                "content": content
            })
        print("  ✅ CNI.pdf chargé")

    # 4. Extract data from documents
    print("\n4️⃣ Extraction des données...")
    extract_request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "form3916_extract",
            "arguments": {
                "documents": documents,
                "user_context": "J'ai ouvert un compte Revolut pour mon usage personnel."
            }
        }
    }
    response = await server.handle_request(extract_request)
    if "error" in response:
        print(f"❌ Erreur: {response['error']}")
    else:
        result = response['result']['content'][0]['text']
        print(result)

    # 5. Get status
    print("\n5️⃣ Statut actuel...")
    status_request = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "form3916_status",
            "arguments": {}
        }
    }
    response = await server.handle_request(status_request)
    print(response['result']['content'][0]['text'])

    # 6. Complete with user data
    print("\n6️⃣ Ajout des données utilisateur...")
    complete_request = {
        "jsonrpc": "2.0",
        "id": 5,
        "method": "tools/call",
        "params": {
            "name": "form3916_complete",
            "arguments": {
                "user_data": {
                    "date_naissance": "29/01/1998",
                    "lieu_naissance": "Ploërmel",
                    "adresse_complete": "135 impasse du Planay, 74210 DOUSSARD",
                    "lieu_signature": "Doussard"
                },
                "skip_optional": True
            }
        }
    }
    response = await server.handle_request(complete_request)
    print(response['result']['content'][0]['text'])

    # 7. Generate PDF
    print("\n7️⃣ Génération du PDF...")
    generate_request = {
        "jsonrpc": "2.0",
        "id": 6,
        "method": "tools/call",
        "params": {
            "name": "form3916_generate",
            "arguments": {
                "format": "url"  # Save to file instead of base64
            }
        }
    }
    response = await server.handle_request(generate_request)
    if "error" in response:
        print(f"❌ Erreur: {response['error']}")
    else:
        print(response['result']['content'][0]['text'])

    # 8. List resources
    print("\n8️⃣ Ressources disponibles...")
    resources_request = {
        "jsonrpc": "2.0",
        "id": 7,
        "method": "resources/list",
        "params": {}
    }
    response = await server.handle_request(resources_request)
    resources = response['result']['resources']
    print(f"✅ {len(resources)} ressources disponibles:")
    for resource in resources:
        print(f"   - {resource['name']}: {resource['uri']}")

    print("\n" + "=" * 70)
    print("✅ TEST TERMINÉ AVEC SUCCÈS!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_mcp_server())