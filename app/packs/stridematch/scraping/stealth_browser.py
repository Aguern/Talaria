"""
Module A: Stealth Browser Navigation
=====================================

Ce module gère la navigation furtive avec Playwright pour éviter les détections anti-bot.
Il implémente des mesures stealth maximales pour passer les protections Cloudflare.

Usage:
    from stealth_browser import get_page_content

    html = await get_page_content("https://runrepeat.com/nike-pegasus-41")
"""

import asyncio
import random
from playwright.async_api import async_playwright, Page, Browser
from typing import Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# User-Agent réaliste (Chrome dernière version sur macOS)
REALISTIC_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)


async def _inject_stealth(page: Page) -> None:
    """
    Injecte les scripts stealth dans la page avant le chargement.

    Cette fonction désactive tous les indicateurs d'automation
    et ajoute des propriétés réalistes au navigator.
    """

    # Script stealth principal
    stealth_js = """
    () => {
        // 1. Masquer webdriver
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });

        // 2. Ajouter des plugins réalistes
        Object.defineProperty(navigator, 'plugins', {
            get: () => [
                {
                    0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format"},
                    description: "Portable Document Format",
                    filename: "internal-pdf-viewer",
                    length: 1,
                    name: "Chrome PDF Plugin"
                },
                {
                    0: {type: "application/pdf", suffixes: "pdf", description: ""},
                    description: "",
                    filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                    length: 1,
                    name: "Chrome PDF Viewer"
                },
                {
                    0: {type: "application/x-nacl", suffixes: "", description: "Native Client Executable"},
                    description: "Native Client Executable",
                    filename: "internal-nacl-plugin",
                    length: 2,
                    name: "Native Client"
                }
            ],
        });

        // 3. Languages réalistes
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en', 'fr'],
        });

        // 4. Hardware réaliste
        Object.defineProperty(navigator, 'hardwareConcurrency', {
            get: () => 8,
        });

        Object.defineProperty(navigator, 'deviceMemory', {
            get: () => 8,
        });

        // 5. Platform
        Object.defineProperty(navigator, 'platform', {
            get: () => 'MacIntel',
        });

        // 6. Supprimer les traces Playwright
        delete window.playwright;
        delete window._playwrightInstance;
        delete window.__playwright;
        delete window.__pw_manual;

        // 7. Chrome runtime
        window.chrome = {
            runtime: {},
            loadTimes: function() {},
            csi: function() {},
            app: {}
        };

        // 8. Permissions réalistes
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );

        // 9. WebGL Vendor réaliste
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) {
                return 'Intel Inc.';
            }
            if (parameter === 37446) {
                return 'Intel Iris OpenGL Engine';
            }
            return getParameter.apply(this, [parameter]);
        };

        // 10. Battery API (éviter les valeurs suspectes)
        if (navigator.getBattery) {
            navigator.getBattery = () => Promise.resolve({
                charging: true,
                chargingTime: 0,
                dischargingTime: Infinity,
                level: 1,
                addEventListener: () => {},
                removeEventListener: () => {},
                dispatchEvent: () => true,
            });
        }
    }
    """

    await page.add_init_script(stealth_js)
    logger.debug("✅ Stealth scripts injected")


async def _simulate_human_behavior(page: Page) -> None:
    """
    Simule un comportement humain : mouvements de souris et scrolling.

    Args:
        page: Page Playwright
    """
    try:
        # Obtenir les dimensions de la page
        dimensions = await page.evaluate("""
            () => ({
                width: document.documentElement.scrollWidth,
                height: document.documentElement.scrollHeight
            })
        """)

        # Mouvement de souris aléatoire
        for _ in range(random.randint(2, 4)):
            x = random.randint(100, min(1000, dimensions['width'] - 100))
            y = random.randint(100, min(800, dimensions['height'] - 100))

            await page.mouse.move(x, y)
            await asyncio.sleep(random.uniform(0.1, 0.3))

        # Scroll aléatoire
        scroll_amount = random.randint(200, 500)
        await page.evaluate(f"window.scrollBy(0, {scroll_amount})")
        await asyncio.sleep(random.uniform(0.5, 1.0))

        # Scroll back up un peu
        await page.evaluate(f"window.scrollBy(0, -{scroll_amount // 2})")
        await asyncio.sleep(random.uniform(0.3, 0.7))

        logger.debug("✅ Human behavior simulated")

    except Exception as e:
        logger.warning(f"⚠️  Could not simulate human behavior: {e}")


async def get_page_content(
    url: str,
    wait_for_selector: Optional[str] = None,
    wait_time: int = 3,
    simulate_human: bool = True
) -> str:
    """
    Récupère le contenu HTML complet d'une page après rendu JavaScript.

    Cette fonction utilise Playwright avec des mesures stealth maximales
    pour éviter la détection anti-bot.

    Args:
        url: URL de la page à scraper
        wait_for_selector: Sélecteur CSS à attendre (optionnel)
        wait_time: Temps d'attente supplémentaire après chargement (secondes)
        simulate_human: Si True, simule des mouvements de souris et scrolling

    Returns:
        HTML complet de la page après rendu

    Raises:
        Exception: Si la page ne peut pas être chargée

    Example:
        >>> html = await get_page_content("https://runrepeat.com/nike-pegasus-41")
        >>> print(len(html))
        150000
    """

    logger.info(f"🌐 Fetching: {url}")

    async with async_playwright() as p:
        # Lancer le navigateur avec options anti-détection
        browser: Browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
                '--disable-features=IsolateOrigins,site-per-process',
                '--window-size=1920,1080',
            ]
        )

        try:
            # Créer un contexte avec fingerprint réaliste
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent=REALISTIC_USER_AGENT,
                locale='en-US',
                timezone_id='America/New_York',
                permissions=[],
                # Headers réalistes
                extra_http_headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Cache-Control': 'max-age=0',
                }
            )

            # Créer une nouvelle page
            page = await context.new_page()

            # Injecter les scripts stealth
            await _inject_stealth(page)

            # Délai aléatoire avant navigation (simuler un humain)
            await asyncio.sleep(random.uniform(1.0, 2.5))

            # Naviguer vers la page
            response = await page.goto(
                url,
                wait_until='networkidle',
                timeout=30000
            )

            if response is None:
                raise Exception(f"Failed to load {url}")

            status = response.status
            logger.info(f"📥 Response status: {status}")

            if status == 403:
                logger.error("❌ 403 Forbidden - Anti-bot detected")
                raise Exception("403 Forbidden - Stealth measures insufficient")

            if status >= 400:
                raise Exception(f"HTTP {status} error")

            # Attendre un sélecteur spécifique si fourni
            if wait_for_selector:
                logger.debug(f"⏳ Waiting for selector: {wait_for_selector}")
                await page.wait_for_selector(wait_for_selector, timeout=10000)

            # Attendre le rendu JavaScript
            await asyncio.sleep(wait_time)

            # Simuler un comportement humain
            if simulate_human:
                await _simulate_human_behavior(page)

            # Récupérer le HTML complet
            html = await page.content()

            logger.info(f"✅ Successfully fetched {len(html)} characters")

            return html

        finally:
            await browser.close()


async def test_stealth():
    """
    Test la configuration stealth sur runrepeat.com
    """
    try:
        html = await get_page_content(
            "https://runrepeat.com",
            wait_time=5,
            simulate_human=True
        )

        print(f"\n{'='*60}")
        print(f"✅ SUCCESS - Fetched {len(html)} characters")
        print(f"{'='*60}")
        print("\nFirst 500 characters:")
        print(html[:500])

        # Vérifier si on a été bloqué
        if "403" in html or "forbidden" in html.lower():
            print("\n❌ BLOCKED - Anti-bot detected")
        else:
            print("\n✅ NOT BLOCKED - Stealth working!")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")


if __name__ == "__main__":
    # Test direct du module
    asyncio.run(test_stealth())
