# 📝 Éditeur de Devis - DéMé Traiteur

## 🎯 Vue d'ensemble

L'**Éditeur de Devis** est un outil web simple et intuitif qui permet d'affiner manuellement les lignes de devis d'une prestation après que le workflow automatique ait été exécuté.

### Fonctionnalités

- ✅ Charger n'importe quelle prestation par son ID Notion
- ✅ Visualiser tous les produits du catalogue (Produits + RH)
- ✅ Modifier les quantités des lignes existantes
- ✅ Ajouter de nouvelles lignes au devis
- ✅ Supprimer des lignes du devis
- ✅ Synchronisation automatique avec Notion
- ✅ Modifications illimitées pour une même prestation

---

## 🚀 Accès à l'éditeur

### URL de l'éditeur

**En local :**
```
http://localhost:8000/api/packs/deme-traiteur/editor
```

**Sur Render (production) :**
```
https://votre-app.onrender.com/api/packs/deme-traiteur/editor
```

---

## 📖 Guide d'utilisation

### Étape 1 : Obtenir l'ID de la prestation

1. Ouvrez la page Notion de la prestation que vous souhaitez éditer
2. Copiez l'ID depuis l'URL de la page

**Format de l'URL Notion :**
```
https://www.notion.so/workspace/Nom-Prestation-12ee0019fd5c48c6b18ce28be4151cf1
                                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                                          ID de la prestation
```

**Exemple d'ID :**
```
12ee0019fd5c48c6b18ce28be4151cf1
```

### Étape 2 : Charger la prestation

1. Collez l'ID dans le champ "ID de la Prestation"
2. Cliquez sur **"📥 Charger"**
3. Le catalogue complet s'affiche avec les lignes existantes pré-cochées

### Étape 3 : Modifier les lignes

**Ajouter un produit :**
- Cochez la case du produit souhaité
- Ajustez la quantité dans le champ numérique

**Modifier une quantité :**
- Changez directement la valeur dans le champ de quantité
- La case se coche/décoche automatiquement

**Supprimer un produit :**
- Décochez la case
- OU mettez la quantité à 0

### Étape 4 : Filtrer le catalogue

Utilisez les filtres pour faciliter la navigation :
- **Tous les items** : Affiche tous les produits
- **Produits Catalogue** : Uniquement les produits alimentaires
- **Ressources Humaines** : Chef et Assistants uniquement

### Étape 5 : Valider les modifications

1. Vérifiez vos modifications
2. Cliquez sur **"✅ Valider et synchroniser avec Notion"**
3. Attendez la confirmation de synchronisation

Le système effectuera automatiquement :
- ✅ Création des nouvelles lignes
- ✅ Mise à jour des quantités modifiées
- ✅ Suppression des lignes décochées

---

## 🔄 Workflow d'utilisation

### Option A : Édition post-workflow (RECOMMANDÉE)

```
1. Client remplit le formulaire
   ↓
2. Workflow automatique s'exécute (10 étapes)
   - Création client/prestation
   - Création lignes de devis automatiques
   - Calcul RH
   - Création Google Sheet
   - Notification email
   ↓
3. [PLUS TARD] Admin ouvre l'éditeur
   ↓
4. Admin affine manuellement les lignes
   ↓
5. Validation → Synchronisation Notion
```

### Modifications multiples

Vous pouvez modifier une même prestation autant de fois que nécessaire :
- Rechargez la prestation avec son ID
- Effectuez de nouvelles modifications
- Validez à nouveau

---

## 🛠️ Architecture technique

### Endpoints API

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/packs/deme-traiteur/editor` | GET | Interface HTML de l'éditeur |
| `/api/packs/deme-traiteur/catalogue` | GET | Liste tous les items du catalogue |
| `/api/packs/deme-traiteur/lignes/{prestation_id}` | GET | Lignes de devis existantes |
| `/api/packs/deme-traiteur/lignes/{prestation_id}` | POST | Mise à jour en masse des lignes |

### Données Notion manipulées

**Base "Catalogue" (lecture seule) :**
- Récupère : Nom, Prix, Type
- Filtre : Tous les types (Produit catalogue + RH)

**Base "Lignes de Devis" (lecture/écriture) :**
- **Création** : Nouvelle ligne avec relation vers Prestation et Item
- **Mise à jour** : Modification de la propriété "Quantité"
- **Suppression** : Archive (soft delete) via `archived: true`

### Propriétés des lignes de devis

Chaque ligne créée/modifiée contient :
```json
{
  "Description": "Nom du produit",
  "Prestation": relation vers la prestation,
  "Item du catalogue": relation vers l'item,
  "Quantité": nombre
}
```

---

## 🧪 Tests en local

### 1. Lancer le serveur

```bash
cd /home/user/Talaria
uvicorn app.main:app --reload --port 8000
```

### 2. Accéder à l'éditeur

```
http://localhost:8000/api/packs/deme-traiteur/editor
```

### 3. Vérifier les logs

Les logs structurés affichent toutes les opérations :
```
Retrieved 25 catalogue items
Retrieved 8 devis lines for prestation 12ee0019...
Created new ligne for item abc123...
Updated ligne def456 with quantite=75
Deleted ligne ghi789
```

---

## 🌐 Déploiement sur Render

### Variables d'environnement requises

L'éditeur utilise les mêmes variables que le pack DéMé Traiteur :

```env
NOTION_API_TOKEN=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
NOTION_DATABASE_CATALOGUE_ID=c9c12290234d4fbaa3198584c0117a5d
NOTION_DATABASE_LIGNES_DEVIS_ID=3bd15e699ed649c189bf437f8057e67e
```

### Fichiers modifiés pour l'éditeur

```
/app/packs/deme_traiteur/
├── integrations/
│   └── notion_client.py          # ✅ Méthodes ajoutées (5 nouvelles)
├── templates/
│   └── devis_editor.html         # ✅ Interface HTML
├── static/
│   └── devis_editor.css          # ✅ Styles CSS
├── router.py                      # ✅ 4 nouveaux endpoints
└── EDITEUR_DEVIS_README.md       # ✅ Cette documentation

/app/main.py                       # ✅ Configuration StaticFiles
```

### Pas de redéploiement nécessaire

L'éditeur est automatiquement disponible dès que le code est déployé sur Render.

---

## 🔍 Dépannage

### Problème : "Erreur lors de la récupération du catalogue"

**Causes possibles :**
- Token Notion invalide
- Database ID incorrect
- Permissions Notion insuffisantes

**Solution :**
Vérifiez les variables d'environnement dans Render :
```bash
NOTION_API_TOKEN
NOTION_DATABASE_CATALOGUE_ID
```

### Problème : "Erreur lors de la récupération des lignes de devis"

**Causes possibles :**
- ID de prestation incorrect
- Prestation n'existe pas dans Notion

**Solution :**
- Vérifiez que l'ID copié est complet (32 caractères)
- Testez l'accès à la page Notion directement

### Problème : Fichiers CSS non chargés

**Cause :**
Le dossier `static/` n'est pas monté correctement

**Solution :**
Vérifiez les logs au démarrage :
```
static files mounted path=/home/user/Talaria/app/packs/deme_traiteur/static
```

---

## 📊 Limites et considérations

### Limites actuelles

- ❌ Pas de synchronisation automatique du Google Sheet après édition
- ❌ Pas d'historique des modifications (audit trail)
- ❌ Pas de validation des quantités max/min

### Améliorations futures possibles

- 🔜 Recalcul automatique du Google Sheet après édition
- 🔜 Historique des modifications par utilisateur
- 🔜 Validation intelligente des quantités (ex: max = PAX × 2)
- 🔜 Aperçu du total du devis en temps réel
- 🔜 Export PDF du devis finalisé

---

## 📞 Support

Pour toute question ou problème :
1. Vérifiez les logs dans Render
2. Testez l'endpoint `/health` pour vérifier que le serveur fonctionne
3. Utilisez l'API docs : `https://votre-app.onrender.com/api/docs`

---

## ✅ Checklist de mise en production

- [x] Code déployé sur Render
- [x] Variables d'environnement Notion configurées
- [x] Accès à l'éditeur vérifié : `/api/packs/deme-traiteur/editor`
- [x] Test complet : charger prestation → modifier → valider
- [x] Vérification dans Notion que les modifications sont bien synchronisées

---

**Version :** 1.0.0
**Date :** Novembre 2025
**Auteur :** Claude Code Assistant
