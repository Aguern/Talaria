"""
Module B: HTML Cleaner
=======================

Ce module nettoie le HTML brut pour le rendre optimal pour l'extraction par IA.
Il supprime tout le contenu inutile (scripts, styles, images) et ne garde que
la structure sémantique et le texte.

Usage:
    from html_cleaner import clean_html

    raw_html = "<html>...</html>"
    clean_text = clean_html(raw_html)
"""

from bs4 import BeautifulSoup, Comment
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Tags à supprimer complètement (avec leur contenu)
TAGS_TO_REMOVE = [
    'script',       # JavaScript
    'style',        # CSS inline
    'noscript',     # Fallback sans JS
    'iframe',       # Frames
    'object',       # Flash, etc.
    'embed',        # Embedded content
    'svg',          # SVG graphics
    'canvas',       # Canvas graphics
    'img',          # Images (ne gardent que le alt)
    'video',        # Videos
    'audio',        # Audio
    'picture',      # Picture elements
    'map',          # Image maps
    'area',         # Area dans image maps
    'meta',         # Meta tags
    'link',         # CSS links
    'form',         # Formulaires (souvent inutiles pour scraping)
    'input',        # Inputs
    'button',       # Buttons
    'select',       # Select boxes
    'textarea',     # Text areas
    'nav',          # Navigation (souvent bruit)
    'footer',       # Footer (souvent bruit)
    'header',       # Header (peut contenir menu)
]

# Tags à garder (structure et contenu)
TAGS_TO_KEEP = [
    # Structure principale
    'main', 'article', 'section', 'aside',

    # Titres
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',

    # Conteneurs
    'div', 'span', 'p',

    # Listes
    'ul', 'ol', 'li', 'dl', 'dt', 'dd',

    # Tableaux (utiles pour specs)
    'table', 'thead', 'tbody', 'tfoot', 'tr', 'th', 'td',

    # Texte sémantique
    'strong', 'b', 'em', 'i', 'mark', 'small', 'del', 'ins',
    'sub', 'sup', 'code', 'pre', 'blockquote', 'cite',

    # Liens (garder le texte, pas nécessairement l'URL)
    'a',

    # Autres éléments de contenu
    'time', 'address', 'abbr', 'dfn', 'kbd', 'samp', 'var',
]


def clean_html(
    html: str,
    keep_attributes: bool = False,
    keep_links: bool = False,
    min_text_length: int = 3
) -> str:
    """
    Nettoie le HTML brut pour l'extraction par IA.

    Supprime tous les éléments non-textuels (scripts, styles, images, etc.)
    et ne garde que la structure sémantique avec le contenu textuel.

    Args:
        html: HTML brut à nettoyer
        keep_attributes: Si True, garde les attributs class/id (défaut: False)
        keep_links: Si True, garde les URLs dans les liens <a> (défaut: False)
        min_text_length: Longueur minimale de texte pour garder un élément

    Returns:
        HTML nettoyé, optimisé pour l'IA

    Example:
        >>> html = '<html><head><script>alert("hi")</script></head><body><h1>Title</h1></body></html>'
        >>> clean = clean_html(html)
        >>> print(clean)
        <h1>Title</h1>
    """

    logger.debug(f"🧹 Cleaning HTML ({len(html)} chars)")

    # Parser avec BeautifulSoup
    soup = BeautifulSoup(html, 'lxml')

    # 1. Supprimer les commentaires HTML
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    # 2. Supprimer tous les tags inutiles
    for tag_name in TAGS_TO_REMOVE:
        for tag in soup.find_all(tag_name):
            tag.decompose()  # Supprime le tag ET son contenu

    # 3. Nettoyer les attributs (garder seulement class/id si demandé)
    if not keep_attributes:
        for tag in soup.find_all(True):  # Tous les tags
            # Garder seulement href si keep_links=True
            if keep_links and tag.name == 'a' and tag.has_attr('href'):
                href = tag['href']
                tag.attrs = {'href': href}
            else:
                tag.attrs = {}

    # 4. Supprimer les tags vides ou avec très peu de texte
    def has_meaningful_content(tag) -> bool:
        """Vérifie si un tag a du contenu significatif"""
        if tag.name in ['br', 'hr']:  # Tags auto-fermants OK
            return True

        text = tag.get_text(strip=True)

        # Garder si assez de texte
        if len(text) >= min_text_length:
            return True

        # Garder si contient des enfants avec du contenu
        if tag.find_all(True):  # A des enfants
            return any(has_meaningful_content(child) for child in tag.find_all(True, recursive=False))

        return False

    # Parcourir récursivement et supprimer les tags vides
    for tag in soup.find_all(True):
        if not has_meaningful_content(tag):
            tag.decompose()

    # 5. Normaliser les espaces blancs
    for tag in soup.find_all(string=True):
        if tag.string:
            # Remplacer les multiples espaces par un seul
            normalized = ' '.join(tag.string.split())
            tag.replace_with(normalized)

    # 6. Extraire seulement le body (ou main si existe)
    main = soup.find('main') or soup.find('article') or soup.find('body')
    if main:
        soup = main

    # Convertir en string
    cleaned = str(soup)

    # 7. Post-processing : supprimer les lignes vides multiples
    lines = cleaned.split('\n')
    lines = [line.strip() for line in lines if line.strip()]
    cleaned = '\n'.join(lines)

    logger.info(f"✅ Cleaned HTML: {len(html)} → {len(cleaned)} chars ({100 * len(cleaned) / len(html):.1f}%)")

    return cleaned


def extract_text_only(html: str) -> str:
    """
    Extrait uniquement le texte du HTML, sans balises.

    Utile si vous voulez envoyer du texte pur à l'IA au lieu de HTML.

    Args:
        html: HTML à convertir en texte

    Returns:
        Texte pur sans balises HTML

    Example:
        >>> html = '<div><h1>Title</h1><p>Content</p></div>'
        >>> text = extract_text_only(html)
        >>> print(text)
        Title
        Content
    """

    # Nettoyer d'abord
    cleaned = clean_html(html)

    # Parser
    soup = BeautifulSoup(cleaned, 'lxml')

    # Extraire le texte
    text = soup.get_text(separator='\n', strip=True)

    # Normaliser les espaces blancs
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    text = '\n'.join(lines)

    logger.info(f"✅ Extracted text: {len(text)} chars")

    return text


def get_structured_content(html: str) -> dict:
    """
    Extrait le contenu de manière structurée (titres, paragraphes, listes, tableaux).

    Retourne un dictionnaire avec la structure du document.

    Args:
        html: HTML à analyser

    Returns:
        Dict avec la structure du contenu

    Example:
        >>> html = '<h1>Title</h1><p>Para 1</p><p>Para 2</p>'
        >>> content = get_structured_content(html)
        >>> print(content)
        {
            'title': 'Title',
            'paragraphs': ['Para 1', 'Para 2'],
            'lists': [],
            'tables': []
        }
    """

    cleaned = clean_html(html)
    soup = BeautifulSoup(cleaned, 'lxml')

    result = {
        'title': None,
        'headings': [],
        'paragraphs': [],
        'lists': [],
        'tables': [],
    }

    # Titre principal (h1)
    h1 = soup.find('h1')
    if h1:
        result['title'] = h1.get_text(strip=True)

    # Tous les titres (h2-h6)
    for level in range(2, 7):
        for heading in soup.find_all(f'h{level}'):
            result['headings'].append({
                'level': level,
                'text': heading.get_text(strip=True)
            })

    # Paragraphes
    for p in soup.find_all('p'):
        text = p.get_text(strip=True)
        if text:
            result['paragraphs'].append(text)

    # Listes
    for ul in soup.find_all(['ul', 'ol']):
        items = [li.get_text(strip=True) for li in ul.find_all('li', recursive=False)]
        result['lists'].append({
            'type': 'ordered' if ul.name == 'ol' else 'unordered',
            'items': items
        })

    # Tableaux
    for table in soup.find_all('table'):
        rows = []
        for tr in table.find_all('tr'):
            cells = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
            rows.append(cells)

        result['tables'].append(rows)

    logger.info(f"✅ Extracted structured content: {len(result['paragraphs'])} paragraphs, {len(result['tables'])} tables")

    return result


# Test du module
if __name__ == "__main__":
    # HTML de test
    test_html = """
    <html>
        <head>
            <title>Test Page</title>
            <script>alert('test');</script>
            <style>.test { color: red; }</style>
        </head>
        <body>
            <nav>
                <a href="/home">Home</a>
                <a href="/about">About</a>
            </nav>

            <main>
                <h1>Nike Pegasus 41</h1>

                <div class="rating">
                    <span>Rating: 4.5/5</span>
                </div>

                <img src="shoe.jpg" alt="Nike Pegasus 41">

                <section class="specs">
                    <h2>Specifications</h2>
                    <table>
                        <tr>
                            <th>Property</th>
                            <th>Value</th>
                        </tr>
                        <tr>
                            <td>Weight</td>
                            <td>280g</td>
                        </tr>
                        <tr>
                            <td>Drop</td>
                            <td>10mm</td>
                        </tr>
                    </table>
                </section>

                <section class="pros-cons">
                    <h3>Pros</h3>
                    <ul>
                        <li>Comfortable cushioning</li>
                        <li>Durable outsole</li>
                        <li>Good value</li>
                    </ul>

                    <h3>Cons</h3>
                    <ul>
                        <li>Heavy for racing</li>
                        <li>Limited color options</li>
                    </ul>
                </section>
            </main>

            <footer>
                <p>Copyright 2024</p>
            </footer>

            <script>console.log('tracking');</script>
        </body>
    </html>
    """

    print("="*60)
    print("TEST MODULE B: HTML CLEANER")
    print("="*60)

    # Test 1: Nettoyage basique
    print("\n1. CLEANED HTML:")
    print("-"*60)
    cleaned = clean_html(test_html)
    print(cleaned[:500])

    # Test 2: Texte pur
    print("\n2. TEXT ONLY:")
    print("-"*60)
    text = extract_text_only(test_html)
    print(text)

    # Test 3: Contenu structuré
    print("\n3. STRUCTURED CONTENT:")
    print("-"*60)
    structured = get_structured_content(test_html)
    import json
    print(json.dumps(structured, indent=2))

    print("\n" + "="*60)
    print("✅ Module B tests completed!")
    print("="*60)
