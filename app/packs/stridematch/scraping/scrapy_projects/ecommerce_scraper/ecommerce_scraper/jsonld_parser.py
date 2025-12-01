"""
JSON-LD Parser - E-commerce Scraper

Utility for parsing schema.org/Product structured data from e-commerce sites.

Most modern e-commerce sites embed product information in JSON-LD format
following the schema.org/Product specification.
"""

import json
import re
from typing import Optional, Dict, List, Any


def extract_jsonld(response) -> List[Dict[str, Any]]:
    """
    Extract all JSON-LD blocks from HTML response.

    Args:
        response: Scrapy response object

    Returns:
        List of parsed JSON-LD dictionaries

    Example:
        >>> jsonld_blocks = extract_jsonld(response)
        >>> product_data = find_product_schema(jsonld_blocks)
    """
    jsonld_blocks = []

    # Extract all <script type="application/ld+json"> blocks
    scripts = response.xpath('//script[@type="application/ld+json"]/text()').getall()

    for script in scripts:
        try:
            data = json.loads(script)
            jsonld_blocks.append(data)
        except json.JSONDecodeError as e:
            # Some sites have malformed JSON-LD
            # Try to clean common issues
            cleaned = script.strip()
            # Remove trailing commas
            cleaned = re.sub(r',\s*}', '}', cleaned)
            cleaned = re.sub(r',\s*]', ']', cleaned)

            try:
                data = json.loads(cleaned)
                jsonld_blocks.append(data)
            except json.JSONDecodeError:
                # Skip if still can't parse
                pass

    return jsonld_blocks


def find_product_schema(jsonld_blocks: List[Dict]) -> Optional[Dict]:
    """
    Find the schema.org/Product block from JSON-LD data.

    Args:
        jsonld_blocks: List of JSON-LD dictionaries

    Returns:
        Product schema dictionary or None

    Example:
        >>> product = find_product_schema(jsonld_blocks)
        >>> product['name']
        "Nike Pegasus 41"
    """
    for block in jsonld_blocks:
        # Check @type field
        schema_type = block.get('@type', '')

        # Handle both string and list types
        if isinstance(schema_type, str):
            schema_type = [schema_type]

        # Look for Product type
        if 'Product' in schema_type:
            return block

        # Handle nested @graph structures (some sites use this)
        if '@graph' in block:
            for item in block['@graph']:
                item_type = item.get('@type', '')
                if isinstance(item_type, str):
                    item_type = [item_type]
                if 'Product' in item_type:
                    return item

    return None


def parse_product_name(product_schema: Dict) -> Optional[str]:
    """
    Extract product name from schema.org/Product.

    Args:
        product_schema: Product JSON-LD dictionary

    Returns:
        Product name or None
    """
    return product_schema.get('name')


def parse_brand(product_schema: Dict) -> Optional[str]:
    """
    Extract brand name from schema.org/Product.

    Args:
        product_schema: Product JSON-LD dictionary

    Returns:
        Brand name or None

    Example:
        >>> parse_brand(product_schema)
        "Nike"
    """
    brand = product_schema.get('brand', {})

    if isinstance(brand, dict):
        return brand.get('name')
    elif isinstance(brand, str):
        return brand

    return None


def parse_model(product_schema: Dict) -> Optional[str]:
    """
    Extract model name from schema.org/Product.

    Args:
        product_schema: Product JSON-LD dictionary

    Returns:
        Model name or None

    Strategy:
        1. Try 'model' field
        2. Try 'mpn' (Manufacturer Part Number)
        3. Extract from product name
    """
    # Try direct model field
    model = product_schema.get('model')
    if model:
        return model

    # Try MPN (Manufacturer Part Number)
    mpn = product_schema.get('mpn')
    if mpn:
        return mpn

    # Try to extract from product name
    product_name = product_schema.get('name', '')
    brand = parse_brand(product_schema)

    if brand and product_name:
        # Remove brand from product name to get model
        model = product_name.replace(brand, '').strip()
        return model

    return None


def parse_offers(product_schema: Dict) -> List[Dict]:
    """
    Extract offers (variants with prices) from schema.org/Product.

    Args:
        product_schema: Product JSON-LD dictionary

    Returns:
        List of offer dictionaries

    Example:
        >>> offers = parse_offers(product_schema)
        >>> offers[0]
        {
            'color': 'Black',
            'size': '42',
            'price': 140.0,
            'currency': 'EUR',
            'availability': 'InStock',
            'url': 'https://...'
        }
    """
    offers_data = product_schema.get('offers', {})
    offers = []

    # Handle single offer
    if isinstance(offers_data, dict):
        offers_data = [offers_data]

    # Handle multiple offers
    for offer in offers_data:
        offer_type = offer.get('@type', '')

        # AggregateOffer contains multiple offers
        if 'AggregateOffer' in offer_type:
            nested_offers = offer.get('offers', [])
            if isinstance(nested_offers, dict):
                nested_offers = [nested_offers]
            offers.extend(nested_offers)
        else:
            offers.append(offer)

    # Parse each offer
    parsed_offers = []
    for offer in offers:
        parsed_offer = {
            'price': _parse_price(offer.get('price')),
            'currency': offer.get('priceCurrency', 'EUR'),
            'availability': offer.get('availability', ''),
            'url': offer.get('url', ''),
            'sku': offer.get('sku', ''),
        }

        # Try to extract color and size from offer name or itemOffered
        item_offered = offer.get('itemOffered', {})
        if isinstance(item_offered, dict):
            parsed_offer['color'] = item_offered.get('color')
            parsed_offer['size'] = item_offered.get('size')

        parsed_offers.append(parsed_offer)

    return parsed_offers


def parse_availability(availability_str: str) -> str:
    """
    Normalize schema.org availability to our enum.

    Args:
        availability_str: Schema.org availability (e.g., "https://schema.org/InStock")

    Returns:
        "in_stock", "out_of_stock", or "preorder"
    """
    if not availability_str:
        return 'in_stock'

    availability_lower = availability_str.lower()

    if 'instock' in availability_lower or 'available' in availability_lower:
        return 'in_stock'
    elif 'outofstock' in availability_lower or 'soldout' in availability_lower:
        return 'out_of_stock'
    elif 'preorder' in availability_lower:
        return 'preorder'
    else:
        return 'in_stock'


def parse_image_url(product_schema: Dict) -> Optional[str]:
    """
    Extract primary image URL from schema.org/Product.

    Args:
        product_schema: Product JSON-LD dictionary

    Returns:
        Image URL or None
    """
    image = product_schema.get('image')

    if isinstance(image, str):
        return image
    elif isinstance(image, list) and len(image) > 0:
        # Return first image
        first_img = image[0]
        if isinstance(first_img, str):
            return first_img
        elif isinstance(first_img, dict):
            return first_img.get('url')

    return None


def parse_description(product_schema: Dict) -> Optional[str]:
    """
    Extract product description from schema.org/Product.

    Args:
        product_schema: Product JSON-LD dictionary

    Returns:
        Description text or None
    """
    return product_schema.get('description')


def _parse_price(price_value: Any) -> Optional[float]:
    """
    Parse price from various formats.

    Args:
        price_value: Price as string, int, or float

    Returns:
        Price as float or None
    """
    if price_value is None:
        return None

    if isinstance(price_value, (int, float)):
        return float(price_value)

    if isinstance(price_value, str):
        # Remove currency symbols and spaces
        price_str = price_value.replace('€', '').replace('EUR', '').replace(',', '.').strip()

        try:
            return float(price_str)
        except ValueError:
            # Try extracting first number
            match = re.search(r'\d+\.?\d*', price_str)
            if match:
                return float(match.group())

    return None


def extract_product_data(response) -> Optional[Dict]:
    """
    Main function to extract all product data from response.

    Args:
        response: Scrapy response object

    Returns:
        Dictionary with extracted product data or None

    Example:
        >>> product_data = extract_product_data(response)
        >>> product_data['brand']
        "Nike"
        >>> product_data['model']
        "Pegasus 41"
    """
    jsonld_blocks = extract_jsonld(response)
    product_schema = find_product_schema(jsonld_blocks)

    if not product_schema:
        return None

    return {
        'full_name': parse_product_name(product_schema),
        'brand_name': parse_brand(product_schema),
        'model_name': parse_model(product_schema),
        'description': parse_description(product_schema),
        'image_url': parse_image_url(product_schema),
        'offers': parse_offers(product_schema),
    }
