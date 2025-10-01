# Fichier: app/tools/data_extractor.py
# VERSION 3.0 - MODÈLE DE DONNÉES EXPERT

from typing import Optional
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from .document_classifier import DocumentType
try:
    from ..core.config import settings
except ImportError:
    from core.config import settings

# VERSION 3.0 - MODÈLE DE DONNÉES EXPERT
class ExtractedData(BaseModel):
    """Modèle de données expert pour le formulaire 3916."""
    nom: Optional[str] = Field(description="Le nom de famille (patronymique) du déclarant.")
    prenom: Optional[str] = Field(description="Le(s) prénom(s) du déclarant.")
    date_naissance: Optional[str] = Field(description="La date de naissance au format JJ.MM.AAAA.")
    lieu_naissance: Optional[str] = Field(description="La ville (et le pays si hors de France) de naissance.")
    adresse_complete: Optional[str] = Field(description="L'adresse complète au 1er janvier (numéro, rue, code postal, ville, pays).")
    numero_compte: Optional[str] = Field(description="Le numéro complet du compte (IBAN pour un compte bancaire).")
    designation_etablissement: Optional[str] = Field(description="Le nom commercial de l'organisme gestionnaire (ex: BNP Paribas, Binance).")
    adresse_etablissement: Optional[str] = Field(description="L'adresse complète de l'organisme gestionnaire.")
    date_ouverture: Optional[str] = Field(description="La date d'ouverture du compte au format JJ.MM.AAAA.")
    date_cloture: Optional[str] = Field(description="La date de clôture si applicable, au format JJ.MM.AAAA.")
    nature_compte: Optional[str] = Field(description="La nature du compte. Doit être une des valeurs suivantes: 'COMPTE_BANCAIRE', 'COMPTE_ACTIFS_NUMERIQUES', 'CONTRAT_ASSURANCE_VIE'.")
    usage_compte: Optional[str] = Field(description="L'usage du compte. Doit être une des valeurs suivantes: 'PERSONNEL', 'PROFESSIONNEL', 'MIXTE'.")

    # Champs supplémentaires pour compatibilité V2.0
    adresse: Optional[str] = Field(description="Alias pour adresse_complete")
    iban: Optional[str] = Field(description="Alias pour numero_compte")
    bic: Optional[str] = Field(description="Le code BIC (Bank Identifier Code)")
    bank_name: Optional[str] = Field(description="Alias pour designation_etablissement")
    account_holder_name: Optional[str] = Field(description="Le nom du titulaire du compte")
    numero_fiscal: Optional[str] = Field(description="Le numéro fiscal de référence")

async def extract_data_from_document(text: str, doc_type: DocumentType) -> ExtractedData:
    llm = ChatOpenAI(model=settings.OPENAI_MODEL, temperature=settings.OPENAI_TEMPERATURE)
    structured_llm = llm.with_structured_output(ExtractedData)

    instruction_specifique = ""
    if doc_type == DocumentType.CNI:
        instruction_specifique = """Tu analyses une carte d'identité française.
        EXTRAIS PRÉCISÉMENT:
        - Le nom de famille (après 'Nom:' ou similaire)
        - Le(s) prénom(s) (après 'Prénom(s):' ou similaire)
        - La date de naissance (format JJ.MM.AAAA ou JJ/MM/AAAA, convertir au format JJ.MM.AAAA)
        - Le lieu de naissance (ville et département/pays)
        - L'adresse complète si présente

        IMPORTANT: Extrais les valeurs EXACTES telles qu'elles apparaissent sur le document."""

    elif doc_type == DocumentType.RIB:
        instruction_specifique = """Tu analyses un RIB (Relevé d'Identité Bancaire).
        EXTRAIS PRÉCISÉMENT:
        - L'IBAN complet (commence par FR et contient 27 caractères) -> stocke dans 'numero_compte' ET 'iban'
        - Le code BIC/SWIFT s'il est présent
        - Le nom de la banque ET l'agence de domiciliation -> stocke dans 'designation_etablissement' ET 'bank_name'
        - Le nom du titulaire du compte -> stocke dans 'account_holder_name'
        - L'adresse du titulaire si présente -> stocke dans 'adresse_complete' ET 'adresse'

        Pour l'adresse de l'établissement bancaire (adresse_etablissement):
        - Si une adresse postale complète est présente, l'extraire
        - Si seulement le nom de la ville est présent (ex: ANGERS), construire une adresse générique:
          "Agence [VILLE], France" (ex: "Agence Angers, France")
        - Si aucune information n'est présente, laisser vide

        IMPORTANT: L'IBAN doit être stocké dans le champ 'numero_compte' pour le formulaire 3916."""

    # Instruction pour les documents non reconnus mais contenant potentiellement des infos bancaires
    if doc_type == DocumentType.INCONNU:
        instruction_specifique = """Tu analyses un document qui peut contenir des informations bancaires ou personnelles.
        RECHERCHE ET EXTRAIS:
        - Un IBAN (commence par 2 lettres puis des chiffres, ex: FR76...) -> stocke dans 'numero_compte' ET 'iban'
        - Un code BIC/SWIFT (8 ou 11 caractères, ex: REVOFRP2)
        - Le nom d'une banque ou établissement -> stocke dans 'designation_etablissement' ET 'bank_name'
        - L'adresse de la banque -> stocke dans 'adresse_etablissement'
        - Un nom de bénéficiaire/titulaire -> stocke dans 'account_holder_name'
        - Toute information personnelle (nom, prénom, adresse, date de naissance, etc.)

        INDICES À CHERCHER:
        - Les mots "IBAN", "BIC", "SWIFT", "Bénéficiaire", "Titulaire", "Nom", "Adresse"
        - Des formats de numéros de compte (lettres + chiffres)
        - Des noms de banques connus (Revolut, BNP, Société Générale, etc.)

        Si tu trouves un IBAN, c'est un compte bancaire donc nature_compte = 'COMPTE_BANCAIRE'"""

    prompt = f"""
    Tu es un expert en extraction de données de documents officiels français.
    Analyse attentivement le texte suivant et extrais TOUTES les informations disponibles.

    {instruction_specifique}

    Règles importantes:
    1. Extrais les valeurs EXACTEMENT comme elles apparaissent dans le document
    2. Pour les dates, convertis au format JJ.MM.AAAA (avec des points)
    3. Pour les comptes bancaires, utilise toujours 'COMPTE_BANCAIRE' comme nature_compte
    4. Pour l'usage, utilise 'PERSONNEL' par défaut
    5. Ne laisse un champ vide QUE si l'information n'est vraiment pas présente
    6. CHERCHE ACTIVEMENT les informations bancaires (IBAN, BIC, nom de banque)

    TEXTE DU DOCUMENT :
    ---
    {text}
    ---
    """

    result = await structured_llm.ainvoke(prompt)

    # Post-traitement pour s'assurer que les données critiques sont bien remplies
    if doc_type == DocumentType.RIB:
        # S'assurer que l'IBAN est dans numero_compte
        if result.iban and not result.numero_compte:
            result.numero_compte = result.iban
        # S'assurer que le nom de banque est dans designation_etablissement
        if result.bank_name and not result.designation_etablissement:
            result.designation_etablissement = result.bank_name
        # Définir la nature du compte
        if not result.nature_compte:
            result.nature_compte = "COMPTE_BANCAIRE"
        if not result.usage_compte:
            result.usage_compte = "PERSONNEL"
        # Si pas d'adresse établissement mais on a le nom avec une ville, créer une adresse générique
        if not result.adresse_etablissement and result.designation_etablissement:
            # Extraire la ville si présente (ex: "BNPPARB ANGERS (00201)" -> "Angers")
            import re
            match = re.search(r'\b([A-Z][A-Z]+)\b', result.designation_etablissement)
            if match and len(match.group(1)) > 3:  # Ville probable
                ville = match.group(1).capitalize()
                result.adresse_etablissement = f"Agence {ville}, France"

    elif doc_type == DocumentType.CNI:
        # Pour une CNI, on peut déduire l'usage personnel
        if not result.usage_compte:
            result.usage_compte = "PERSONNEL"

    return result


# Maintenir compatibilité avec V2.0
from typing import Optional as TypingOptional

class RIBData(BaseModel):
    """Modèle de données pour les informations d'un RIB - DEPRECATED, utilisez ExtractedData."""
    iban: TypingOptional[str] = Field(description="L'IBAN complet du compte, ex: FR7630004000031234567890143")
    bic: TypingOptional[str] = Field(description="Le code BIC (Bank Identifier Code), ex: BNPAFRPPXXX")
    bank_name: TypingOptional[str] = Field(description="Le nom de l'établissement bancaire, ex: BNP Paribas")
    account_holder_name: TypingOptional[str] = Field(description="Le nom du titulaire du compte")

async def extract_rib_data(text: str) -> RIBData:
    """
    DEPRECATED: Utilisez extract_data_from_document avec DocumentType.RIB.
    Fonction de compatibilité pour l'ancienne API.
    """
    extracted_data = await extract_data_from_document(text, DocumentType.RIB)

    return RIBData(
        iban=extracted_data.iban,
        bic=extracted_data.bic,
        bank_name=extracted_data.bank_name,
        account_holder_name=extracted_data.account_holder_name
    )