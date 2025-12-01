"""
Test RTINGS.com accessibility with Playwright
Extract running shoe data from RTINGS dynamically loaded pages
"""

import asyncio
from playwright.async_api import async_playwright
from undetected_playwright import stealth_async


async def test_rtings():
    """Test RTINGS.com running shoes page"""

    print("=" * 70)
    print("🧪 Testing RTINGS.com - Running Shoes Database")
    print("=" * 70)

    async with async_playwright() as p:
        print("\n🌐 Launching browser with stealth mode...")

        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
            ]
        )

        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        )

        page = await context.new_page()
        await stealth_async(page)

        try:
            # Test main page
            print("\n📡 Loading RTINGS main running shoes page...")
            await page.goto('https://www.rtings.com/running-shoes', wait_until='networkidle', timeout=30000)

            print(f"✅ Page loaded: {page.url}")
            print(f"Status: Page accessible\n")

            # Wait for content to load
            await page.wait_for_timeout(3000)

            # Try to find shoe links
            print("🔍 Searching for shoe review links...")
            links = await page.locator('a[href*="/running-shoes/reviews/"]').all()

            print(f"Found {len(links)} review links\n")

            if len(links) > 0:
                print("First 10 shoe URLs:")
                for i, link in enumerate(links[:10]):
                    href = await link.get_attribute('href')
                    text = await link.text_content()
                    print(f"  {i+1}. {text.strip() if text else 'N/A'} → {href}")

            # Test table tool
            print("\n" + "-" * 70)
            print("📊 Testing Table Tool page...")
            await page.goto('https://www.rtings.com/running-shoes/tools/table', wait_until='networkidle', timeout=30000)

            await page.wait_for_timeout(5000)  # Wait for dynamic content

            # Check if table loaded
            print("🔍 Looking for data table...")

            # Try multiple selectors
            table = await page.locator('table').count()
            rows = await page.locator('tr').count()

            print(f"Tables found: {table}")
            print(f"Table rows found: {rows}")

            # Try to extract any visible shoe data
            if rows > 0:
                print("\nExtracting sample data...")
                cells = await page.locator('td').all()
                print(f"Total cells: {len(cells)}")

                if len(cells) > 0:
                    print("\nFirst 20 cell contents:")
                    for i, cell in enumerate(cells[:20]):
                        content = await cell.text_content()
                        print(f"  Cell {i+1}: {content.strip() if content else 'empty'}")

            # Check for paywall
            print("\n🔒 Checking for paywall...")
            paywall = await page.locator('text=/subscribe|premium|unlock/i').count()
            print(f"Paywall elements found: {paywall}")

            print("\n" + "=" * 70)
            print("✅ RTINGS Test Complete")
            print("=" * 70)

        except Exception as e:
            print("\n" + "=" * 70)
            print("❌ Error occurred")
            print("=" * 70)
            print(f"Error: {e}")

        finally:
            await browser.close()


if __name__ == '__main__':
    asyncio.run(test_rtings())
