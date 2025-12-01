"""
Script d'inspection i-run.fr

Lance Scrapy avec un User-Agent réaliste pour inspecter la structure HTML.
"""

import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.http import TextResponse

class IrunInspector(scrapy.Spider):
    name = 'irun_inspector'

    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 2,
        'LOG_LEVEL': 'INFO',
    }

    start_urls = [
        'https://www.i-run.fr/chaussures-running-route-homme/',
    ]

    def parse(self, response):
        print("\n" + "="*60)
        print("INSPECTION i-run.fr - Structure HTML")
        print("="*60 + "\n")

        # Check JSON-LD
        jsonld_scripts = response.xpath('//script[@type="application/ld+json"]/text()').getall()
        if jsonld_scripts:
            print(f"✅ JSON-LD trouvé : {len(jsonld_scripts)} block(s)")
            print(f"Premier bloc (100 premiers caractères) :")
            print(jsonld_scripts[0][:100] + "...")
        else:
            print("❌ Pas de JSON-LD trouvé")

        print("\n" + "-"*60)

        # Try common selectors for product cards
        selectors_to_test = [
            ('div.product-card', 'Cards avec .product-card'),
            ('div.product-item', 'Cards avec .product-item'),
            ('article.product', 'Articles produit'),
            ('div[class*="product"]', 'Divs contenant "product"'),
            ('a[href*="/produit"]', 'Liens vers produits'),
            ('a[href*="-m/"]', 'Liens finissant par -m/ (homme)'),
        ]

        print("\n🔍 Test de sélecteurs pour produits :")
        for selector, description in selectors_to_test:
            elements = response.css(selector)
            count = len(elements)
            print(f"  {selector:40s} → {count:3d} éléments ({description})")

        print("\n" + "-"*60)

        # Try pagination selectors
        pagination_selectors = [
            ('a.next', 'Bouton next avec classe .next'),
            ('a.pagination-next', 'Pagination next'),
            ('link[rel="next"]', 'Link rel=next'),
            ('a[aria-label*="suivant"]', 'Lien avec "suivant"'),
        ]

        print("\n🔍 Test de sélecteurs pour pagination :")
        for selector, description in pagination_selectors:
            elements = response.css(selector)
            count = len(elements)
            if count > 0:
                href = elements[0].attrib.get('href', 'N/A')
                print(f"  ✅ {selector:40s} → href: {href[:50]}")
            else:
                print(f"  ❌ {selector:40s} → 0 élément")

        print("\n" + "-"*60)

        # Extract first product link if found
        product_links = []
        for selector, _ in selectors_to_test:
            if 'a[href' in selector:
                product_links = response.css(selector + '::attr(href)').getall()
                if product_links:
                    print(f"\n✅ Liens produits trouvés avec {selector}")
                    print(f"Premier lien : {product_links[0]}")
                    print(f"Total : {len(product_links)} liens")
                    break

        if not product_links:
            print("\n❌ Aucun lien produit trouvé avec les sélecteurs testés")
            print("\n📝 Extrait du HTML (500 premiers caractères) :")
            print(response.text[:500])

        print("\n" + "="*60)
        print("Fin de l'inspection")
        print("="*60 + "\n")

if __name__ == '__main__':
    process = CrawlerProcess()
    process.crawl(IrunInspector)
    process.start()
