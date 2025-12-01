#!/usr/bin/env python3
"""
Script de débogage POC 2 - Inspection détaillée des recommandations.
"""

import pandas as pd
import numpy as np
import scipy.sparse as sp
from lightfm import LightFM
from lightfm.cross_validation import random_train_test_split
from sklearn.neighbors import NearestNeighbors
import warnings
warnings.filterwarnings('ignore')

print("="*70)
print("DEBUG POC 2 - Inspection Détaillée")
print("="*70)
print()

# Configuration
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

# Générer les mêmes données que run_poc2.py
n_items = 100
n_users = 500

print("📊 Génération des données...")

items_df = pd.DataFrame({
    'item_id': range(n_items),
    'feature_stabilite': np.random.choice(
        ['neutral', 'stable', 'motion_control'], n_items, p=[0.5, 0.35, 0.15]
    ),
    'feature_amorti': np.random.choice(['low', 'medium', 'high'], n_items, p=[0.2, 0.5, 0.3]),
    'feature_drop': np.random.choice(['low', 'medium', 'high'], n_items, p=[0.3, 0.5, 0.2])
})

users_df = pd.DataFrame({
    'user_id': range(n_users),
    'feature_pronation': np.random.choice(
        ['neutral', 'overpronation', 'supination'], n_users, p=[0.5, 0.35, 0.15]
    ),
    'feature_foulee': np.random.choice(
        ['heel_strike', 'midfoot_strike', 'forefoot_strike'], n_users, p=[0.6, 0.3, 0.1]
    ),
    'feature_poids': np.random.choice(['light', 'medium', 'heavy'], n_users, p=[0.25, 0.50, 0.25])
})

print(f"✅ {n_users} utilisateurs et {n_items} items générés")
print()

# Fonction de compatibilité biomécanique (copie de run_poc2.py)
def calculate_biomechanical_match(user, item):
    score = 0
    # Règle 1
    if user['feature_pronation'] == 'overpronation':
        if item['feature_stabilite'] == 'motion_control':
            score += 2
        elif item['feature_stabilite'] == 'stable':
            score += 1
        elif item['feature_stabilite'] == 'neutral':
            score -= 2
    elif user['feature_pronation'] == 'neutral':
        if item['feature_stabilite'] == 'neutral':
            score += 1
        elif item['feature_stabilite'] == 'motion_control':
            score -= 1
    elif user['feature_pronation'] == 'supination':
        if item['feature_stabilite'] == 'neutral':
            score += 2
        elif item['feature_stabilite'] in ['stable', 'motion_control']:
            score -= 1
    # Règle 2
    if user['feature_poids'] == 'heavy':
        if item['feature_amorti'] == 'high':
            score += 1
        elif item['feature_amorti'] == 'low':
            score -= 1
    elif user['feature_poids'] == 'light':
        if item['feature_amorti'] == 'low':
            score += 1
        elif item['feature_amorti'] == 'high':
            score -= 1
    # Règle 3
    if user['feature_foulee'] == 'forefoot_strike':
        if item['feature_drop'] == 'low':
            score += 1
    elif user['feature_foulee'] == 'heel_strike':
        if item['feature_drop'] == 'high':
            score += 1

    if score >= 1:
        return 1
    elif score <= -1:
        return -1
    else:
        return 0

print("🔍 INSPECTION DÉTAILLÉE - 3 Utilisateurs")
print("="*70)

# Sélectionner 3 utilisateurs représentatifs
sample_users = [
    users_df[users_df['feature_pronation'] == 'overpronation'].iloc[0],
    users_df[users_df['feature_pronation'] == 'neutral'].iloc[0],
    users_df[users_df['feature_pronation'] == 'supination'].iloc[0]
]

for i, user in enumerate(sample_users):
    print(f"\n{'='*70}")
    print(f"UTILISATEUR #{user['user_id']}")
    print(f"{'='*70}")
    print(f"  Profil Biomécanique:")
    print(f"    - Pronation : {user['feature_pronation']}")
    print(f"    - Foulée    : {user['feature_foulee']}")
    print(f"    - Poids     : {user['feature_poids']}")
    print()

    # Calculer les scores de compatibilité avec TOUS les items
    compatibility_scores = []
    for _, item in items_df.iterrows():
        score = calculate_biomechanical_match(user, item)
        compatibility_scores.append({
            'item_id': item['item_id'],
            'stabilite': item['feature_stabilite'],
            'amorti': item['feature_amorti'],
            'drop': item['feature_drop'],
            'biomech_score': score
        })

    compat_df = pd.DataFrame(compatibility_scores)

    # Statistiques
    n_excellent = (compat_df['biomech_score'] == 1).sum()
    n_bad = (compat_df['biomech_score'] == -1).sum()
    n_neutral = (compat_df['biomech_score'] == 0).sum()

    print(f"  Compatibilité avec les {n_items} items du catalogue:")
    print(f"    ✅ Excellents matches (score=1) : {n_excellent} items ({n_excellent/n_items*100:.1f}%)")
    print(f"    ⚠️  Neutres (score=0)           : {n_neutral} items ({n_neutral/n_items*100:.1f}%)")
    print(f"    ❌ Mauvais matches (score=-1)   : {n_bad} items ({n_bad/n_items*100:.1f}%)")
    print()

    # Afficher les top-10 items idéaux
    print(f"  🏆 TOP-10 ITEMS IDÉAUX (selon règles biomécaniques):")
    top10_ideal = compat_df.sort_values('biomech_score', ascending=False).head(10)
    for idx, row in top10_ideal.iterrows():
        score_emoji = "✅" if row['biomech_score'] == 1 else ("⚠️" if row['biomech_score'] == 0 else "❌")
        print(f"    {score_emoji} Item #{row['item_id']:3d} - {row['stabilite']:15s} {row['amorti']:6s} {row['drop']:6s} (score={row['biomech_score']:+d})")
    print()

print("\n" + "="*70)
print("ANALYSE DU PROBLÈME")
print("="*70)
print()

print("🚨 PROBLÈME IDENTIFIÉ #1 : Le kNN Baseline est cassé")
print("-"*70)
print("Le kNN actuel recommande basé sur la SIMILARITÉ DES ITEMS,")
print("mais IGNORE complètement le profil biomécanique de l'utilisateur.")
print()
print("Exemple:")
print("  - Utilisateur avec overpronation achète une chaussure 'neutral' par erreur")
print("  - kNN dit: 'Voici d'autres chaussures neutral similaires'")
print("  - Résultat: Le kNN recommande des chaussures DANGEREUSES ❌")
print()

print("🚨 PROBLÈME IDENTIFIÉ #2 : Sparsité extrême")
print("-"*70)
print("Avec 5463 interactions pour 500 users × 100 items = 50000 cellules,")
print("seulement 10.9% de la matrice est remplie.")
print()
print("Impact:")
print("  - Chaque utilisateur a ~11 interactions en moyenne")
print("  - Split 80/20: ~9 en train, ~2 en test")
print("  - Pour Precision@10: on recommande 10 items, mais seulement 2-3 'vrais' items dans test")
print("  - Probabilité de hit: 2-3/100 = 2-3% (correspond aux résultats!) ❌")
print()

print("🚨 PROBLÈME IDENTIFIÉ #3 : Évaluation biaisée")
print("-"*70)
print("Si un utilisateur avec overpronation a:")
print("  - 2 chaussures 'stable' dans le test set")
print("  - Le modèle recommande 8 autres chaussures 'stable' (excellents matches!)")
print("  - Mais ces 8 ne sont pas dans le test set")
print("  - Résultat: Precision = 2/10 = 20% alors que les recommandations sont bonnes! ❌")
print()

print("="*70)
print("💡 SOLUTIONS PROPOSÉES")
print("="*70)
print()
print("1. Refondre le Baseline:")
print("   - Remplacer kNN par un 'Rule-Based Biomechanical Matcher'")
print("   - Calculer score de compatibilité: user_profile × item_features")
print("   - Recommander les top-10 items avec meilleur score")
print()
print("2. Augmenter drastiquement les interactions:")
print("   - Passer de 10K à 50K interactions")
print("   - Objectif: 100 interactions/user (dense)")
print()
print("3. Optimiser LightFM:")
print("   - Réduire no_components: 30 → 10")
print("   - Augmenter epochs: 30 → 50")
print("   - Ajouter régularisation")
print()
print("4. (Optionnel) Changer la métrique:")
print("   - Évaluer sur 'vérité terrain biomécanique'")
print("   - Au lieu du test set historique")
print()
print("="*70)
