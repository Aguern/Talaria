# Prompt pour mise à jour de la base Notion Catalogue

## Contexte
Tu dois mettre à jour la base Notion "Catalogue" avec les nouvelles options de menu pour le traiteur DéMé.

## Informations de la base
- **ID de la base** : `c9c12290234d4fbaa3198584c0117a5d`
- **Nom** : Catalogue
- **Colonnes existantes** :
  - Nom (Title) - Requis
  - Prix (Number) - Requis

## Tâches à effectuer

### 1. Ajouter les 8 nouveaux items

Crée 8 nouvelles entrées dans la base Catalogue avec les informations suivantes :

| Nom | Prix (€ HT) |
|-----|-------------|
| Antipasti froids (burrata, salade, carapaccio, etc.) | **À DÉFINIR** |
| Antipasti chauds (fritures, arancini, crispy mozza, etc.) | **À DÉFINIR** |
| Pizza (sur-mesure) | **À DÉFINIR** |
| Pâtes (Truffes, Carbonara, Ragù, etc.) | **À DÉFINIR** |
| Risotto (champignon, fruits de mer, 4 fromages, etc.) | **À DÉFINIR** |
| Desserts (Tiramisù, Panna cotta, crème pistache) | **À DÉFINIR** |
| Planches (charcuterie, fromage) | **À DÉFINIR** |
| Boissons (soft, vin, cocktail) | **À DÉFINIR** |

### 2. Gérer les anciens items (OPTIONNEL)

Les anciens items sont :
- Entrées (Charcuterie et Fromages)
- Pâtes (Truffes, Carbonara, Ragù,...)
- Desserts (Tiramisù, Panna cotta, Canollis)

**Options** :
- **Option A (Recommandée)** : Créer une colonne "Actif" (type: Checkbox) et marquer les nouveaux comme actifs, les anciens comme inactifs
- **Option B** : Supprimer les anciens items (perte d'historique)
- **Option C** : Les garder tels quels (peut créer de la confusion)

## Instructions pour Claude Desktop (avec MCP Notion)

```
Connecte-toi à la base Notion avec l'ID : c9c12290234d4fbaa3198584c0117a5d

1. Ajoute 8 nouvelles pages avec ces propriétés :
   - Page 1: Nom = "Antipasti froids (burrata, salade, carapaccio, etc.)", Prix = 0
   - Page 2: Nom = "Antipasti chauds (fritures, arancini, crispy mozza, etc.)", Prix = 0
   - Page 3: Nom = "Pizza (sur-mesure)", Prix = 0
   - Page 4: Nom = "Pâtes (Truffes, Carbonara, Ragù, etc.)", Prix = 0
   - Page 5: Nom = "Risotto (champignon, fruits de mer, 4 fromages, etc.)", Prix = 0
   - Page 6: Nom = "Desserts (Tiramisù, Panna cotta, crème pistache)", Prix = 0
   - Page 7: Nom = "Planches (charcuterie, fromage)", Prix = 0
   - Page 8: Nom = "Boissons (soft, vin, cocktail)", Prix = 0

2. (OPTIONNEL) Crée une colonne "Actif" (type: Checkbox) si elle n'existe pas déjà

3. (OPTIONNEL) Marque les 8 nouveaux items comme Actif = true

4. Liste-moi tous les items de la base pour vérification
```

## Instructions pour modification manuelle (sans MCP)

1. Ouvre la base Catalogue dans Notion
2. Clique sur "+ New" pour créer 8 nouvelles entrées
3. Pour chaque entrée, remplis :
   - **Nom** : Exactement comme indiqué dans le tableau ci-dessus
   - **Prix** : Mets 0 temporairement (à définir ensuite avec DéMé)
4. (Optionnel) Ajoute une propriété "Actif" (type: Checkbox)
5. Garde les anciens items ou marque-les comme inactifs

## ⚠️ Points d'attention

1. **Les noms doivent être EXACTEMENT identiques** aux valeurs des formulaires (casse, accents, parenthèses)
2. **Ne supprime pas les anciens items** sans backup préalable
3. **Les prix à 0 doivent être mis à jour** avant de passer en production
4. **Vérifie qu'il n'y a pas de doublons** après l'ajout

## Vérification post-modification

Après la modification, vérifie que :
- [ ] Les 8 nouveaux items sont créés
- [ ] Les noms correspondent exactement aux options du formulaire
- [ ] La colonne "Prix" existe pour tous les items (même si = 0)
- [ ] Aucun doublon n'existe
- [ ] (Si Option A choisie) La colonne "Actif" existe et est bien configurée

## Prochaine étape

Une fois la base Notion mise à jour :
1. Définis les prix réels avec DéMé
2. Teste le workflow avec un formulaire de test
3. Vérifie que les lignes de devis se créent correctement dans Notion
