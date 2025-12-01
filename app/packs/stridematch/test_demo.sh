#!/bin/bash
# Script de test automatique pour le POC StrideMatch
# Ce script télécharge une vidéo YouTube et lance l'analyse

set -e  # Exit on error

echo "============================================================"
echo "StrideMatch POC - Script de Test Automatique"
echo "============================================================"
echo ""

# Configuration
YOUTUBE_URL="https://youtu.be/w_g1i6tzNGk"
VIDEO_OUTPUT="test_running_download.mp4"
ANALYSIS_OUTPUT="test_running_analyzed.mp4"
PACK_DIR="/Users/nicolasangougeard/Desktop/SaaS_NR/app/packs/stridematch"

# Étape 1: Vérifier les dépendances Python
echo "📦 Vérification des dépendances Python..."
python3 -c "import cv2" 2>/dev/null || {
    echo "❌ OpenCV manquant. Installation..."
    pip install opencv-python
}

python3 -c "import mediapipe" 2>/dev/null || {
    echo "❌ MediaPipe manquant. Installation..."
    pip install mediapipe
}

python3 -c "import scipy" 2>/dev/null || {
    echo "❌ SciPy manquant. Installation..."
    pip install scipy
}

python3 -c "import numpy" 2>/dev/null || {
    echo "❌ NumPy manquant. Installation..."
    pip install numpy
}

echo "✅ Toutes les dépendances Python sont installées"
echo ""

# Étape 2: Installer yt-dlp si nécessaire
echo "📥 Vérification de yt-dlp..."
if ! command -v yt-dlp &> /dev/null; then
    echo "❌ yt-dlp non trouvé. Installation..."
    pip install yt-dlp
else
    echo "✅ yt-dlp est installé"
fi
echo ""

# Étape 3: Télécharger la vidéo YouTube
echo "🎥 Téléchargement de la vidéo depuis YouTube..."
echo "URL: $YOUTUBE_URL"
cd "$PACK_DIR"

if [ -f "$VIDEO_OUTPUT" ]; then
    echo "⚠️  La vidéo existe déjà. Suppression..."
    rm "$VIDEO_OUTPUT"
fi

yt-dlp -f "best[height<=720]" "$YOUTUBE_URL" -o "$VIDEO_OUTPUT" --quiet --no-warnings

if [ ! -f "$VIDEO_OUTPUT" ]; then
    echo "❌ Échec du téléchargement de la vidéo"
    exit 1
fi

echo "✅ Vidéo téléchargée: $VIDEO_OUTPUT"
echo ""

# Étape 4: Lancer l'analyse
echo "🔬 Lancement de l'analyse biomécanique..."
echo "Mode: detailed"
echo "Sortie: $ANALYSIS_OUTPUT"
echo ""

python3 poc1_standalone.py "$VIDEO_OUTPUT" \
    --output "$ANALYSIS_OUTPUT" \
    --mode detailed

echo ""
echo "============================================================"
echo "✅ Test terminé avec succès !"
echo "============================================================"
echo ""
echo "Fichiers générés:"
echo "  - Vidéo source: $PACK_DIR/$VIDEO_OUTPUT"
echo "  - Vidéo analysée: $PACK_DIR/$ANALYSIS_OUTPUT"
echo ""
echo "Pour ouvrir la vidéo analysée:"
echo "  open $PACK_DIR/$ANALYSIS_OUTPUT"
echo ""
