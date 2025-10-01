# Fichier: app/tools/document_classifier.py

import re
from enum import Enum
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
try:
    from ..core.config import settings
except ImportError:
    from core.config import settings

# 1. Utiliser un Enum pour une liste de types de documents centralisée et évolutive.
# Pour ajouter un nouveau type de document, il suffira de l'ajouter ici.
class DocumentType(str, Enum):
    """Types de documents que la plateforme peut identifier."""
    CNI = "Carte Nationale d'Identité"
    RIB = "Relevé d'Identité Bancaire"
    AVIS_IMPOSITION = "Avis d'Imposition sur le Revenu"
    PASSEPORT = "Passeport"
    INCONNU = "Document Inconnu ou Non Pertinent"

# 2. Définir un schéma de sortie Pydantic pour forcer le LLM à choisir parmi nos types.
class ClassificationResult(BaseModel):
    """Schéma de sortie pour le résultat de la classification."""
    document_type: DocumentType = Field(description="Le type du document identifié, choisi EXCLUSIVEMENT dans la liste fournie.")

# 3. Créer la fonction de classification
async def classify_document(text: str) -> DocumentType:
    """
    Identifie le type d'un document à partir de son contenu textuel.

    Args:
        text: Le texte brut extrait du document.

    Returns:
        Un membre de l'Enum DocumentType.
    """
    llm = ChatOpenAI(model=settings.OPENAI_MODEL, temperature=settings.OPENAI_TEMPERATURE)
    structured_llm = llm.with_structured_output(ClassificationResult)

    # AJOUT : Nettoyer le texte pour améliorer la fiabilité
    cleaned_text = re.sub(r'\s+', ' ', text).strip()

    allowed_types_list = [f"- {member.name} ({member.value})" for member in DocumentType if member != DocumentType.INCONNU]
    allowed_types_str = "\n".join(allowed_types_list)

    prompt = f"""
    Ta mission est d'agir comme un archiviste expert. Analyse le texte suivant et identifie précisément son type.

    INDICES POUR L'IDENTIFICATION :
    - Une "Carte Nationale d'Identité" contient les mots "CARTE NATIONALE D'IDENTITÉ" ou "RÉPUBLIQUE FRANÇAISE" ou "Nom:" suivi de "Prénom(s):" et "Date de naissance:"
    - Un "Relevé d'Identité Bancaire" contient les mots "IBAN" et "BIC" ou "RIB" ou "Relevé d'Identité Bancaire"
    - Un "Avis d'Imposition" contient "DIRECTION GÉNÉRALE DES FINANCES PUBLIQUES" ou "AVIS D'IMPÔT"
    - Un "Passeport" contient "PASSEPORT" ou "PASSPORT"

    Tu dois retourner UN SEUL type, choisi exclusivement dans la liste ci-dessous.
    Si le document ne correspond à aucun des types listés ou est ambigu, choisis 'INCONNU'.

    LISTE DES TYPES AUTORISÉS :
    {allowed_types_str}

    TEXTE À ANALYSER (extrait) :
    ---
    {cleaned_text[:2000]}
    ---
    """

    try:
        result = await structured_llm.ainvoke(prompt)
        return result.document_type
    except Exception as e:
        print(f"Erreur lors de la classification du document : {e}")
        return DocumentType.INCONNU