# 🚀 Serveur MCP Form 3916

## 📋 Description

Ce serveur MCP (Model Context Protocol) expose les capacités de traitement du formulaire 3916 via un protocole standardisé, permettant l'intégration avec Claude Desktop et d'autres outils compatibles MCP.

## 🛠️ Installation

### Prérequis
- Python 3.8+
- Toutes les dépendances du projet SaaS (voir requirements.txt)
- Claude Desktop (pour l'intégration)

### Configuration Claude Desktop

1. **Localiser le fichier de configuration Claude Desktop :**
   ```bash
   # macOS
   ~/Library/Application Support/Claude/claude_desktop_config.json

   # Windows
   %APPDATA%\Claude\claude_desktop_config.json

   # Linux
   ~/.config/Claude/claude_desktop_config.json
   ```

2. **Ajouter la configuration du serveur :**

   Copier le contenu de `claude_desktop_config.json` dans votre fichier de configuration Claude Desktop :

   ```json
   {
     "mcpServers": {
       "form3916": {
         "command": "python3",
         "args": [
           "/Users/nicolasangougeard/Desktop/SaaS_NR/app/mcp_server/form3916_server.py"
         ],
         "env": {
           "PYTHONPATH": "/Users/nicolasangougeard/Desktop/SaaS_NR",
           "OPENAI_API_KEY": "YOUR_OPENAI_API_KEY"
         }
       }
     }
   }
   ```

   ⚠️ **Important :** Remplacer `YOUR_OPENAI_API_KEY` par votre clé API OpenAI

3. **Redémarrer Claude Desktop** pour prendre en compte la configuration

## 🧪 Test Local

### Test automatisé
```bash
# Depuis le répertoire du projet
python3 app/mcp_server/test_mcp_local.py
```

### Test manuel avec le script de lancement
```bash
# Rendre le script exécutable (première fois seulement)
chmod +x app/mcp_server/launch_mcp.sh

# Lancer le serveur
./app/mcp_server/launch_mcp.sh
```

Le serveur attend ensuite des requêtes JSON-RPC sur stdin.

## 🎯 Utilisation dans Claude Desktop

Une fois configuré, vous pouvez utiliser ces commandes dans Claude Desktop :

### 1. Extraction depuis des documents
```
Utilise l'outil form3916_extract pour extraire les données de mes documents.
Voici mes fichiers : [glisser-déposer les fichiers]
```

### 2. Complétion avec vos données
```
Utilise form3916_complete pour ajouter ces informations :
- Date de naissance : 29/01/1998
- Lieu de naissance : Ploërmel
- Adresse : 135 impasse du Planay, 74210 DOUSSARD
```

### 3. Génération du PDF
```
Génère le PDF final avec form3916_generate
```

### 4. Vérification du statut
```
Quel est le statut actuel avec form3916_status ?
```

## 📚 Outils Disponibles

### `form3916_extract`
Extrait les données depuis des documents (PDF, TXT)
- **Input :** Documents en base64, contexte utilisateur
- **Output :** Données extraites et champs manquants

### `form3916_complete`
Complète le formulaire avec des données utilisateur
- **Input :** Données utilisateur (date/lieu naissance, adresse, etc.)
- **Output :** Confirmation de l'ajout

### `form3916_generate`
Génère le PDF final du formulaire 3916
- **Input :** Format souhaité (base64 ou fichier)
- **Output :** PDF généré

### `form3916_status`
Affiche l'état actuel du traitement
- **Input :** Aucun
- **Output :** Résumé des données et champs manquants

## 🔍 Debugging

### Logs du serveur
Les logs sont affichés dans stderr. Pour les capturer :
```bash
python3 app/mcp_server/form3916_server.py 2> mcp_server.log
```

### Tester une requête JSON-RPC
```bash
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | python3 app/mcp_server/form3916_server.py
```

## 🏗️ Architecture

```
form3916_server.py
├── Form3916MCPServer       # Classe principale
│   ├── handle_request()    # Routeur JSON-RPC
│   ├── list_tools()        # Liste des outils
│   ├── call_tool()         # Exécution des outils
│   └── state management    # Gestion de session
│
└── Intégration avec
    ├── graph_modern.py     # Workflow LangGraph
    ├── adapter_final.py    # Mapping coordonnées PDF
    └── pdf_generator.py    # Génération ReportLab
```

## ⚠️ Limitations Actuelles

1. **Session unique :** Le serveur ne gère qu'une session à la fois
2. **Pas de persistance :** Les données sont perdues au redémarrage
3. **Synchrone pour Claude :** Les opérations longues peuvent bloquer

## 🚀 Prochaines Étapes

- [ ] Support multi-sessions avec identifiants uniques
- [ ] Persistance SQLite des sessions
- [ ] WebSocket pour opérations asynchrones
- [ ] Dashboard de monitoring
- [ ] Support d'autres formulaires fiscaux