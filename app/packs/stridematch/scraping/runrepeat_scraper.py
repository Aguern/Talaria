"""
RunRepeat Scraper - Pipeline Complet
=====================================

Ce script assemble les 3 modules (stealth navigation, HTML cleaning, AI extraction)
pour scraper runrepeat.com avec des mesures anti-détection maximales.

Usage:
    # Scraper une seule chaussure
    python runrepeat_scraper.py https://runrepeat.com/nike-pegasus-41

    # Scraper plusieurs chaussures
    python runrepeat_scraper.py --urls urls.txt

    # Mode test (juste vérifier l'accès)
    python runrepeat_scraper.py --test
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

# Importer nos modules
from stealth_browser import get_page_content
from html_cleaner import clean_html, extract_text_only
from ai_extractor import extract_shoe_data

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def scrape_shoe(url: str, save_raw: bool = False) -> Optional[Dict[str, Any]]:
    """
    Scrape une chaussure complète (navigation + nettoyage + extraction).

    Args:
        url: URL de la page RunRepeat
        save_raw: Si True, sauvegarde le HTML brut et nettoyé

    Returns:
        Dict avec les données extraites, ou None si échec

    Example:
        >>> data = await scrape_shoe("https://runrepeat.com/nike-pegasus-41")
        >>> print(data['model_name'])
        'Nike Pegasus 41'
    """

    logger.info(f"\n{'='*80}")
    logger.info(f"🎯 SCRAPING: {url}")
    logger.info(f"{'='*80}\n")

    try:
        # ÉTAPE 1: Navigation furtive avec Playwright
        logger.info("📥 STEP 1/3: Fetching page with stealth browser...")
        raw_html = await get_page_content(
            url,
            wait_time=5,
            simulate_human=True
        )

        if save_raw:
            filename = f"raw_{url.split('/')[-1]}.html"
            Path(filename).write_text(raw_html, encoding='utf-8')
            logger.info(f"💾 Saved raw HTML to: {filename}")

        # ÉTAPE 2: Nettoyage du HTML
        logger.info("\n🧹 STEP 2/3: Cleaning HTML...")
        cleaned = clean_html(raw_html)

        if save_raw:
            filename = f"cleaned_{url.split('/')[-1]}.html"
            Path(filename).write_text(cleaned, encoding='utf-8')
            logger.info(f"💾 Saved cleaned HTML to: {filename}")

        # ÉTAPE 3: Extraction par IA
        logger.info("\n🤖 STEP 3/3: Extracting data with AI...")
        data = await extract_shoe_data(cleaned)

        # Ajouter l'URL source
        data['source_url'] = url

        logger.info(f"\n✅ SUCCESS - Extracted: {data.get('model_name', 'Unknown')}")
        logger.info(f"   Weight: {data.get('weight_g', 'N/A')}g")
        logger.info(f"   Drop: {data.get('drop_mm', 'N/A')}mm")
        logger.info(f"   Score: {data.get('score', 'N/A')}/100")
        logger.info(f"   Pros: {len(data.get('pros', []))} items")
        logger.info(f"   Cons: {len(data.get('cons', []))} items")

        return data

    except Exception as e:
        logger.error(f"\n❌ FAILED to scrape {url}: {e}")
        return None


async def scrape_multiple(urls: List[str], output_file: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Scrape plusieurs chaussures de manière séquentielle.

    Args:
        urls: Liste d'URLs à scraper
        output_file: Chemin du fichier JSON de sortie (optionnel)

    Returns:
        Liste des données extraites

    Example:
        >>> urls = [
        ...     "https://runrepeat.com/nike-pegasus-41",
        ...     "https://runrepeat.com/adidas-ultraboost-23"
        ... ]
        >>> results = await scrape_multiple(urls, "results.json")
    """

    logger.info(f"\n🚀 BATCH SCRAPING: {len(urls)} shoes")

    results = []

    for i, url in enumerate(urls, 1):
        logger.info(f"\n[{i}/{len(urls)}] Processing: {url}")

        data = await scrape_shoe(url)

        if data:
            results.append(data)

        # Délai entre chaque requête (être poli)
        if i < len(urls):
            delay = 10  # 10 secondes entre chaque chaussure
            logger.info(f"⏳ Waiting {delay}s before next request...")
            await asyncio.sleep(delay)

    # Sauvegarder si demandé
    if output_file:
        output_path = Path(output_file)
        output_path.write_text(
            json.dumps(results, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
        logger.info(f"\n💾 Saved {len(results)} results to: {output_file}")

    # Résumé
    logger.info(f"\n{'='*80}")
    logger.info(f"📊 BATCH COMPLETE")
    logger.info(f"{'='*80}")
    logger.info(f"Total: {len(urls)} URLs")
    logger.info(f"Success: {len(results)} ({100*len(results)/len(urls):.1f}%)")
    logger.info(f"Failed: {len(urls) - len(results)}")

    return results


async def test_access():
    """
    Test l'accès à RunRepeat (vérifier qu'on n'est pas bloqué).
    """

    logger.info("\n🧪 TESTING ACCESS TO RUNREPEAT.COM")
    logger.info("="*80)

    try:
        html = await get_page_content(
            "https://runrepeat.com",
            wait_time=5,
            simulate_human=True
        )

        # Vérifier si on a été bloqué
        html_lower = html.lower()

        if "403" in html or "forbidden" in html_lower:
            logger.error("\n❌ BLOCKED - 403 Forbidden detected")
            logger.error("Stealth measures are insufficient.")
            return False

        elif "cloudflare" in html_lower and "checking your browser" in html_lower:
            logger.error("\n❌ BLOCKED - Cloudflare challenge detected")
            logger.error("May need residential IP or additional stealth.")
            return False

        else:
            logger.info(f"\n✅ ACCESS OK - Fetched {len(html)} characters")
            logger.info("Stealth configuration appears to be working!")

            # Essayer de nettoyer et voir le contenu
            cleaned = clean_html(html)
            text = extract_text_only(cleaned)

            logger.info(f"\nFirst 500 chars of text content:")
            logger.info("-"*80)
            print(text[:500])

            return True

    except Exception as e:
        logger.error(f"\n❌ TEST FAILED: {e}")
        return False


# CLI Interface
async def main():
    """Point d'entrée principal"""

    import argparse

    parser = argparse.ArgumentParser(
        description="RunRepeat Scraper with Stealth + AI Extraction"
    )

    parser.add_argument(
        'url',
        nargs='?',
        help='Single URL to scrape'
    )

    parser.add_argument(
        '--urls',
        help='File containing list of URLs (one per line)'
    )

    parser.add_argument(
        '--output', '-o',
        default='runrepeat_data.json',
        help='Output JSON file (default: runrepeat_data.json)'
    )

    parser.add_argument(
        '--test',
        action='store_true',
        help='Test access to RunRepeat (no scraping)'
    )

    parser.add_argument(
        '--save-raw',
        action='store_true',
        help='Save raw and cleaned HTML files'
    )

    args = parser.parse_args()

    # Mode test
    if args.test:
        success = await test_access()
        sys.exit(0 if success else 1)

    # Scraping unique
    elif args.url:
        data = await scrape_shoe(args.url, save_raw=args.save_raw)

        if data:
            print("\n" + "="*80)
            print("EXTRACTED DATA:")
            print("="*80)
            print(json.dumps(data, indent=2, ensure_ascii=False))

            # Sauvegarder
            output_path = Path(args.output)
            output_path.write_text(
                json.dumps([data], indent=2, ensure_ascii=False),
                encoding='utf-8'
            )
            print(f"\n💾 Saved to: {args.output}")

            sys.exit(0)
        else:
            sys.exit(1)

    # Scraping multiple
    elif args.urls:
        urls_file = Path(args.urls)
        if not urls_file.exists():
            logger.error(f"❌ File not found: {args.urls}")
            sys.exit(1)

        # Lire les URLs
        urls = [
            line.strip()
            for line in urls_file.read_text().splitlines()
            if line.strip() and not line.startswith('#')
        ]

        if not urls:
            logger.error("❌ No URLs found in file")
            sys.exit(1)

        results = await scrape_multiple(urls, args.output)
        sys.exit(0 if results else 1)

    # Aucun argument
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
