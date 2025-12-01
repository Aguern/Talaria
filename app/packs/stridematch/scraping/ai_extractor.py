"""
Module C: AI-Powered Extraction
================================

Ce module utilise l'API OpenAI (GPT-4o-mini) pour extraire des données structurées
à partir de HTML nettoyé. Fini les sélecteurs CSS fragiles !

Usage:
    from ai_extractor import extract_shoe_data

    cleaned_html = "<h1>Nike Pegasus 41</h1>..."
    data = await extract_shoe_data(cleaned_html)
    print(data['model_name'])  # "Nike Pegasus 41"
"""

import os
import json
import logging
from typing import Optional, Dict, Any
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Schéma Pydantic pour la validation des données extraites
class ShoeData(BaseModel):
    """Schéma de données pour une chaussure de running"""

    model_name: str = Field(
        description="Nom complet du modèle (ex: 'Nike Pegasus 41')"
    )

    score: Optional[float] = Field(
        None,
        description="Note globale (0-100 ou 0-5, sera normalisée)",
        ge=0,
        le=100
    )

    weight_g: Optional[int] = Field(
        None,
        description="Poids en grammes (ex: 280)",
        gt=0
    )

    drop_mm: Optional[float] = Field(
        None,
        description="Drop talon-pointe en millimètres (ex: 10.0)",
        ge=0,
        le=20
    )

    stack_heel_mm: Optional[float] = Field(
        None,
        description="Hauteur de la semelle au talon en mm",
        ge=0
    )

    stack_forefoot_mm: Optional[float] = Field(
        None,
        description="Hauteur de la semelle à l'avant-pied en mm",
        ge=0
    )

    cushioning_softness_ha: Optional[int] = Field(
        None,
        description="Dureté de l'amorti (Shore A hardness, 0-100)",
        ge=0,
        le=100
    )

    energy_return_pct: Optional[float] = Field(
        None,
        description="Pourcentage de retour d'énergie (0-100)",
        ge=0,
        le=100
    )

    flexibility_index: Optional[float] = Field(
        None,
        description="Indice de flexibilité",
        ge=0
    )

    torsional_rigidity_index: Optional[float] = Field(
        None,
        description="Indice de rigidité torsionnelle",
        ge=0
    )

    # Lab Test Results - Shock Absorption
    shock_absorption_heel_sa: Optional[float] = Field(
        None,
        description="Absorption des chocs au talon (SA units)",
        ge=0
    )

    shock_absorption_forefoot_sa: Optional[float] = Field(
        None,
        description="Absorption des chocs à l'avant-pied (SA units)",
        ge=0
    )

    energy_return_forefoot_pct: Optional[float] = Field(
        None,
        description="Retour d'énergie avant-pied (%)",
        ge=0,
        le=100
    )

    # Lab Test Results - Dimensions
    toebox_width_mm: Optional[float] = Field(
        None,
        description="Largeur de la toebox en mm",
        ge=0
    )

    toebox_height_mm: Optional[float] = Field(
        None,
        description="Hauteur de la toebox en mm",
        ge=0
    )

    width_fit_mm: Optional[float] = Field(
        None,
        description="Largeur générale (fit) en mm",
        ge=0
    )

    midsole_width_forefoot_mm: Optional[float] = Field(
        None,
        description="Largeur de la semelle intermédiaire à l'avant-pied en mm",
        ge=0
    )

    midsole_width_heel_mm: Optional[float] = Field(
        None,
        description="Largeur de la semelle intermédiaire au talon en mm",
        ge=0
    )

    # Lab Test Results - Durability & Materials
    traction_coefficient: Optional[float] = Field(
        None,
        description="Coefficient de traction (0-1)",
        ge=0,
        le=1
    )

    toebox_durability_score: Optional[int] = Field(
        None,
        description="Score de durabilité de la toebox (1-5)",
        ge=1,
        le=5
    )

    heel_padding_durability_score: Optional[int] = Field(
        None,
        description="Score de durabilité du rembourrage talon (1-5)",
        ge=1,
        le=5
    )

    outsole_durability_score: Optional[int] = Field(
        None,
        description="Score de durabilité de la semelle extérieure (1-5)",
        ge=1,
        le=5
    )

    outsole_wear_mm: Optional[float] = Field(
        None,
        description="Usure de la semelle après test (mm)",
        ge=0
    )

    outsole_thickness_mm: Optional[float] = Field(
        None,
        description="Épaisseur de la semelle extérieure en mm",
        ge=0
    )

    insole_thickness_mm: Optional[float] = Field(
        None,
        description="Épaisseur de la semelle intérieure en mm",
        ge=0
    )

    tongue_padding_mm: Optional[float] = Field(
        None,
        description="Épaisseur du rembourrage de la languette en mm",
        ge=0
    )

    # Lab Test Results - Temperature & Conditions
    midsole_softness_cold_pct: Optional[float] = Field(
        None,
        description="Changement de dureté à froid (%)",
        ge=0
    )

    breathability_score: Optional[int] = Field(
        None,
        description="Score de respirabilité (1-5)",
        ge=1,
        le=5
    )

    heel_counter_stiffness_score: Optional[int] = Field(
        None,
        description="Score de rigidité du contrefort talon (1-5)",
        ge=1,
        le=5
    )

    # Specs
    arch_support: Optional[str] = Field(
        None,
        description="Type de support de voûte (ex: 'Neutral', 'Stability', 'Motion control')"
    )

    strike_pattern: Optional[str] = Field(
        None,
        description="Type de foulée recommandé (ex: 'Heel', 'Mid/forefoot', 'Heel, Mid/forefoot')"
    )

    pace: Optional[str] = Field(
        None,
        description="Allure recommandée (ex: 'Daily running', 'Tempo', 'Racing')"
    )

    widths_available: Optional[list[str]] = Field(
        None,
        description="Largeurs disponibles (ex: ['Normal', 'Wide', 'X-Wide'])"
    )

    season: Optional[str] = Field(
        None,
        description="Saison recommandée (ex: 'Summer', 'All seasons', 'Winter')"
    )

    removable_insole: Optional[bool] = Field(
        None,
        description="Semelle intérieure amovible (true/false)"
    )

    reflective_elements: Optional[bool] = Field(
        None,
        description="Présence d'éléments réfléchissants (true/false)"
    )

    pros: list[str] = Field(
        default_factory=list,
        description="Liste des points positifs"
    )

    cons: list[str] = Field(
        default_factory=list,
        description="Liste des points négatifs"
    )

    price_usd: Optional[float] = Field(
        None,
        description="Prix en USD",
        gt=0
    )

    brand: Optional[str] = Field(
        None,
        description="Marque (ex: 'Nike', 'Adidas')"
    )

    category: Optional[str] = Field(
        None,
        description="Catégorie (ex: 'road', 'trail', 'racing')"
    )

    gender: Optional[str] = Field(
        None,
        description="Genre (ex: 'male', 'female', 'unisex')"
    )


# Prompt système pour l'extraction
EXTRACTION_SYSTEM_PROMPT = """You are a precise data extraction assistant specialized in running shoes.

Your task is to extract structured data from HTML content of running shoe reviews and specifications.

IMPORTANT RULES:
1. Extract ONLY information that is explicitly present in the content
2. If a field is not found, set it to null (do not guess or invent)
3. For scores: normalize to 0-100 scale (if you see "4.5/5", convert to 90)
4. For weights: extract in grams (if you see "280g" or "9.9oz", extract as integer)
5. For drop: extract in millimeters (if you see "10mm", extract as 10.0)
6. For pros/cons: extract as separate bullet points, clean and concise
7. Be consistent with units (always mm, always grams, always 0-100 for percentages)

LAB TEST RESULTS TO EXTRACT (when available):
- Shock absorption (heel and forefoot in SA units)
- Energy return (heel and forefoot in %)
- Stack heights (heel and forefoot in mm)
- Weight (in grams)
- Drop (in mm)
- Midsole softness (Shore A hardness)
- Flexibility/Stiffness (in Newtons or as index)
- Torsional rigidity (score 1-5 or as index)
- Heel counter stiffness (score 1-5)
- Toebox dimensions (width and height in mm)
- Width/fit (in mm)
- Midsole width (forefoot and heel in mm)
- Traction coefficient (0-1)
- Durability scores (toebox, heel padding, outsole: 1-5)
- Outsole wear (mm) and thickness (mm)
- Insole thickness (mm)
- Tongue padding (mm)
- Breathability (score 1-5)
- Midsole softness change in cold (%)

SPECS TO EXTRACT (when available):
- Brand, category, gender
- Arch support type (Neutral, Stability, etc.)
- Strike pattern (Heel, Mid/forefoot, etc.)
- Pace (Daily running, Tempo, Racing, etc.)
- Widths available (list)
- Season (Summer, All seasons, Winter, etc.)
- Removable insole (true/false)
- Reflective elements (true/false)

Return ONLY valid JSON matching the schema. No explanations, no markdown, just JSON."""


# Client OpenAI (initialisé une seule fois)
_client: Optional[AsyncOpenAI] = None


def get_openai_client() -> AsyncOpenAI:
    """Récupère ou crée le client OpenAI"""
    global _client

    if _client is None:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY not found in environment variables. "
                "Please set it in your .env file."
            )

        _client = AsyncOpenAI(api_key=api_key)
        logger.debug("✅ OpenAI client initialized")

    return _client


async def extract_shoe_data(
    cleaned_html: str,
    model: Optional[str] = None,
    temperature: float = 0.0,
    max_completion_tokens: int = 4000
) -> Dict[str, Any]:
    """
    Extrait les données structurées d'une chaussure à partir de HTML nettoyé.

    Utilise l'API OpenAI avec Structured Outputs pour garantir un JSON valide.

    Args:
        cleaned_html: HTML nettoyé (sortie de html_cleaner.clean_html())
        model: Modèle OpenAI à utiliser (défaut: gpt-5-mini, ou OPENAI_MODEL dans .env)
               Options: 'gpt-5-mini' (rapide/économique), 'gpt-5.1' (tâches agentiques)
        temperature: Température (0.0 = déterministe, recommandé pour extraction)
        max_completion_tokens: Nombre maximum de tokens dans la réponse (GPT-5+)

    Returns:
        Dictionnaire avec les données extraites (validé par Pydantic)

    Raises:
        ValueError: Si l'API key n'est pas configurée
        Exception: Si l'extraction échoue

    Example:
        >>> html = clean_html(raw_html)
        >>> data = await extract_shoe_data(html)
        >>> print(data['model_name'])
        'Nike Pegasus 41'
        >>> print(data['weight_g'])
        280
    """

    # Utiliser GPT-5 mini par défaut (nov 2025) ou depuis env
    if model is None:
        model = os.getenv('OPENAI_MODEL', 'gpt-5-mini')

    logger.info(f"🤖 Extracting shoe data with {model}")
    logger.debug(f"Input length: {len(cleaned_html)} chars")

    client = get_openai_client()

    try:
        # Appel API avec Structured Outputs (beta)
        # Note: GPT-5 mini ne supporte que temperature=1 (défaut)
        response = await client.beta.chat.completions.parse(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": EXTRACTION_SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": f"Extract running shoe data from this HTML:\n\n{cleaned_html}"
                }
            ],
            response_format=ShoeData,  # Force le respect du schéma Pydantic
            max_completion_tokens=max_completion_tokens,
        )

        # Récupérer l'objet parsé
        shoe_data = response.choices[0].message.parsed

        if shoe_data is None:
            raise Exception("Failed to parse response into ShoeData schema")

        # Convertir en dict
        result = shoe_data.model_dump()

        logger.info(f"✅ Extracted data for: {result.get('model_name', 'Unknown')}")
        logger.debug(f"Tokens used: {response.usage.total_tokens}")

        return result

    except Exception as e:
        logger.error(f"❌ Extraction failed: {e}")
        raise


async def extract_shoe_data_fallback(
    cleaned_html: str,
    model: str = "gpt-5-mini"
) -> Dict[str, Any]:
    """
    Méthode de fallback sans Structured Outputs (pour compatibilité).

    Utilise un JSON schema classique au lieu de Pydantic.

    Args:
        cleaned_html: HTML nettoyé
        model: Modèle OpenAI

    Returns:
        Dict avec les données extraites
    """

    logger.info(f"🤖 Extracting shoe data (fallback mode) with {model}")

    client = get_openai_client()

    # Schéma JSON pour forcer la structure
    json_schema = {
        "type": "object",
        "properties": {
            "model_name": {"type": "string"},
            "score": {"type": ["number", "null"]},
            "weight_g": {"type": ["integer", "null"]},
            "drop_mm": {"type": ["number", "null"]},
            "stack_heel_mm": {"type": ["number", "null"]},
            "stack_forefoot_mm": {"type": ["number", "null"]},
            "cushioning_softness_ha": {"type": ["integer", "null"]},
            "energy_return_pct": {"type": ["number", "null"]},
            "flexibility_index": {"type": ["number", "null"]},
            "torsional_rigidity_index": {"type": ["number", "null"]},
            "pros": {"type": "array", "items": {"type": "string"}},
            "cons": {"type": "array", "items": {"type": "string"}},
            "price_usd": {"type": ["number", "null"]},
            "brand": {"type": ["string", "null"]},
            "category": {"type": ["string", "null"]},
            "gender": {"type": ["string", "null"]},
        },
        "required": ["model_name", "pros", "cons"],
        "additionalProperties": False
    }

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": EXTRACTION_SYSTEM_PROMPT + f"\n\nReturn JSON matching this schema:\n{json.dumps(json_schema, indent=2)}"
                },
                {
                    "role": "user",
                    "content": f"Extract running shoe data from this HTML:\n\n{cleaned_html}"
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
        )

        # Parser le JSON de la réponse
        content = response.choices[0].message.content
        if not content:
            raise Exception("Empty response from API")

        result = json.loads(content)

        logger.info(f"✅ Extracted data (fallback): {result.get('model_name', 'Unknown')}")

        return result

    except Exception as e:
        logger.error(f"❌ Fallback extraction failed: {e}")
        raise


async def batch_extract_shoes(
    html_list: list[str],
    model: str = "gpt-5-mini",
    concurrent_limit: int = 5
) -> list[Dict[str, Any]]:
    """
    Extrait les données de plusieurs chaussures en parallèle.

    Args:
        html_list: Liste de HTML nettoyés
        model: Modèle OpenAI
        concurrent_limit: Nombre de requêtes API simultanées

    Returns:
        Liste de dicts avec les données extraites

    Example:
        >>> htmls = [clean_html(html1), clean_html(html2), clean_html(html3)]
        >>> results = await batch_extract_shoes(htmls)
        >>> print(len(results))
        3
    """

    import asyncio

    logger.info(f"🚀 Batch extracting {len(html_list)} shoes (max {concurrent_limit} concurrent)")

    # Semaphore pour limiter les requêtes concurrentes
    semaphore = asyncio.Semaphore(concurrent_limit)

    async def extract_with_limit(html: str) -> Dict[str, Any]:
        async with semaphore:
            try:
                return await extract_shoe_data(html, model=model)
            except Exception as e:
                logger.error(f"Failed to extract: {e}")
                return {}

    # Lancer toutes les extractions en parallèle
    results = await asyncio.gather(*[extract_with_limit(html) for html in html_list])

    successful = sum(1 for r in results if r)
    logger.info(f"✅ Batch extraction complete: {successful}/{len(html_list)} successful")

    return results


# Test du module
if __name__ == "__main__":
    import asyncio

    # HTML de test (simplifié)
    test_html = """
    <main>
        <h1>Nike Pegasus 41</h1>

        <div class="rating">
            <span>Overall Score: 87/100</span>
        </div>

        <section class="specs">
            <h2>Technical Specifications</h2>
            <table>
                <tr>
                    <td>Weight</td>
                    <td>280g (men's size 9)</td>
                </tr>
                <tr>
                    <td>Drop</td>
                    <td>10mm</td>
                </tr>
                <tr>
                    <td>Heel Stack</td>
                    <td>37mm</td>
                </tr>
                <tr>
                    <td>Forefoot Stack</td>
                    <td>27mm</td>
                </tr>
                <tr>
                    <td>Price</td>
                    <td>$140</td>
                </tr>
            </table>
        </section>

        <section>
            <h3>Pros</h3>
            <ul>
                <li>Comfortable and responsive cushioning</li>
                <li>Durable outsole with excellent traction</li>
                <li>Great value for daily training</li>
                <li>Breathable upper keeps feet cool</li>
            </ul>

            <h3>Cons</h3>
            <ul>
                <li>Too heavy for racing (280g)</li>
                <li>Limited color options</li>
                <li>Not ideal for trail running</li>
            </ul>
        </section>
    </main>
    """

    async def test():
        print("="*60)
        print("TEST MODULE C: AI EXTRACTOR")
        print("="*60)

        # Vérifier la clé API
        if not os.getenv('OPENAI_API_KEY'):
            print("\n⚠️  OPENAI_API_KEY not set - skipping test")
            print("Set it in .env: OPENAI_API_KEY=sk-...")
            return

        try:
            # Test extraction
            print("\nExtracting data...")
            data = await extract_shoe_data(test_html)

            print("\n✅ EXTRACTION SUCCESSFUL!")
            print("-"*60)
            print(json.dumps(data, indent=2))

        except Exception as e:
            print(f"\n❌ TEST FAILED: {e}")

    asyncio.run(test())
