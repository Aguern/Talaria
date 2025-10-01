#!/bin/bash

echo "🔍 Diagnostic MCP Form 3916"
echo "============================"

echo -e "\n1. Vérification Docker..."
if docker ps | grep -q "saas_nr-api-1"; then
    echo "✅ Container Docker actif"
else
    echo "❌ Container Docker inactif"
    echo "   Lancez: cd /Users/nicolasangougeard/Desktop/SaaS_NR && docker compose up -d"
    exit 1
fi

echo -e "\n2. Test du serveur MCP..."
RESPONSE=$(echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | \
    /Users/nicolasangougeard/Desktop/SaaS_NR/app/mcp_server/run_form3916_mcp.sh 2>/dev/null)

if echo "$RESPONSE" | grep -q "form3916-server"; then
    echo "✅ Serveur MCP répond correctement"
else
    echo "❌ Serveur MCP ne répond pas"
    echo "   Réponse: $RESPONSE"
    exit 1
fi

echo -e "\n3. Configuration Claude Desktop..."
CONFIG_FILE="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
if [ -f "$CONFIG_FILE" ]; then
    if grep -q "form3916" "$CONFIG_FILE"; then
        echo "✅ Configuration form3916 présente"
        echo "   Path: $(grep -A1 'form3916' "$CONFIG_FILE" | grep command | cut -d'"' -f4)"
    else
        echo "❌ Configuration form3916 absente"
    fi
else
    echo "❌ Fichier de configuration introuvable"
fi

echo -e "\n4. Processus MCP..."
if ps aux | grep -v grep | grep -q "form3916_server.py"; then
    echo "✅ Processus MCP actif"
    ps aux | grep -v grep | grep "form3916_server.py" | head -1
else
    echo "⚠️  Aucun processus MCP actif (normal si Claude Desktop est fermé)"
fi

echo -e "\n5. Test des outils..."
TOOLS=$(echo '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | \
    /Users/nicolasangougeard/Desktop/SaaS_NR/app/mcp_server/run_form3916_mcp.sh 2>/dev/null)

if echo "$TOOLS" | grep -q "form3916_extract"; then
    echo "✅ Outils disponibles:"
    echo "$TOOLS" | grep -o '"name":"[^"]*"' | cut -d'"' -f4 | sed 's/^/   - /'
else
    echo "❌ Outils non disponibles"
fi

echo -e "\n✨ Pour activer dans Claude Desktop:"
echo "   1. Quittez Claude Desktop complètement (Cmd+Q)"
echo "   2. Relancez Claude Desktop"
echo "   3. Testez avec: 'Peux-tu utiliser l'outil form3916_status ?'"