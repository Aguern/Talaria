"""
Analyze RTINGS table structure to identify all available columns
Extract column headers and sample data for scraping strategy
"""

import asyncio
from playwright.async_api import async_playwright
from undetected_playwright import stealth_async


async def analyze_table():
    """Analyze RTINGS table tool structure"""

    print("=" * 70)
    print("📊 Analyzing RTINGS Table Structure")
    print("=" * 70)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
        )

        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )

        page = await context.new_page()
        await stealth_async(page)

        try:
            print("\n📡 Loading table tool...")
            await page.goto('https://www.rtings.com/running-shoes/tools/table', wait_until='networkidle')
            await page.wait_for_timeout(5000)

            # Extract table headers
            print("\n🔍 Extracting table headers...")
            headers = await page.locator('th').all()

            print(f"\nFound {len(headers)} column headers:")
            print("-" * 70)

            header_texts = []
            for i, header in enumerate(headers):
                text = await header.text_content()
                text_clean = text.strip() if text else ''
                header_texts.append(text_clean)
                print(f"  Column {i+1}: {text_clean}")

            # Extract first 5 rows of data
            print("\n" + "-" * 70)
            print("📝 Extracting sample data (first 5 shoes):")
            print("-" * 70)

            rows = await page.locator('tbody tr').all()
            print(f"\nTotal rows found: {len(rows)}")

            for i, row in enumerate(rows[:5]):
                cells = await row.locator('td').all()
                print(f"\n🏃 Shoe {i+1}:")

                row_data = []
                for j, cell in enumerate(cells):
                    content = await cell.text_content()
                    content_clean = content.strip() if content else ''
                    row_data.append(content_clean)

                    # Match with header if available
                    if j < len(header_texts):
                        print(f"  {header_texts[j]}: {content_clean}")
                    else:
                        print(f"  Column {j+1}: {content_clean}")

            # Try to find spec columns (stack, cushioning, drop, etc.)
            print("\n" + "-" * 70)
            print("🔬 Searching for critical lab specs...")
            print("-" * 70)

            keywords = ['stack', 'cushion', 'drop', 'weight', 'energy', 'return', 'heel', 'forefoot']

            for keyword in keywords:
                elements = await page.locator(f'text=/.*{keyword}.*/i').all()
                print(f"\n'{keyword}' mentions: {len(elements)}")

                if len(elements) > 0 and len(elements) < 20:  # Avoid too many results
                    for elem in elements[:5]:
                        text = await elem.text_content()
                        print(f"  - {text.strip() if text else 'N/A'}")

            print("\n" + "=" * 70)
            print("✅ Analysis complete")
            print("=" * 70)

        except Exception as e:
            print(f"\n❌ Error: {e}")

        finally:
            await browser.close()


if __name__ == '__main__':
    asyncio.run(analyze_table())
