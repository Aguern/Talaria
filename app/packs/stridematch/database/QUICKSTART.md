# ⚡ Démarrage Rapide - Test Infrastructure StrideMatch

## 1️⃣ Démarre Docker Desktop
Attends que l'icône Docker soit verte dans la barre de menu.

## 2️⃣ Lance le script de test automatique

```bash
cd /Users/nicolasangougeard/Desktop/SaaS_NR
./app/packs/stridematch/database/test_infrastructure.sh
```

**Durée : ~2 minutes**

## 3️⃣ Teste les modèles SQLAlchemy

```bash
python app/packs/stridematch/database/test_models.py
```

**Résultat attendu : 5/5 tests passés ✅**

---

## C'est tout ! 🎉

Si les 2 scripts se terminent sans erreur, ton infrastructure est prête.

**Prochaines étapes :**
- Phases 3-6 : Projets Scrapy + ETL + Webhook
- Ou commence à scraper des données réelles !

---

## Accès Rapide aux Services

| Service | URL/Commande | Credentials |
|---------|-------------|-------------|
| **PostgreSQL** | `localhost:5432` | Voir `.env` |
| **MongoDB** | `localhost:27017` | `stridematch` / `stridematch_password` |
| **Neo4j** | http://localhost:7474 | `neo4j` / `stridematch_neo4j` |

---

## Besoin d'aide ?

Consulte le guide détaillé : `TEST_GUIDE.md`
