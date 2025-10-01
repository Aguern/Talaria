#!/bin/bash

echo "🧪 Test d'intégration MCP avec Docker"
echo "======================================"

# Test 1: Initialisation
echo -e "\n1️⃣ Test d'initialisation..."
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | docker exec -i saas_nr-api-1 python /app/mcp_server/form3916_server.py

# Test 2: Liste des outils
echo -e "\n\n2️⃣ Test de liste des outils..."
echo '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | docker exec -i saas_nr-api-1 python /app/mcp_server/form3916_server.py

echo -e "\n\n✅ Si vous voyez les réponses JSON ci-dessus, le serveur MCP fonctionne !"
echo "📝 Redémarrez maintenant Claude Desktop pour charger la configuration."