"""
Product name matching utility for cross-source data fusion
Normalizes and matches product names between i-run.fr and RunRepeat
"""

import re
from typing import Optional, Dict, List
from difflib import SequenceMatcher


class ProductMatcher:
    """Match products across different data sources by normalized names"""

    # Common brand name variations
    BRAND_VARIATIONS = {
        'asics': ['asics', 'asics sportsstyle'],
        'nike': ['nike', 'nike running'],
        'adidas': ['adidas', 'adidas running'],
        'new balance': ['new balance', 'nb', 'newbalance'],
        'brooks': ['brooks', 'brooks running'],
        'hoka': ['hoka', 'hoka one one'],
        'saucony': ['saucony'],
        'mizuno': ['mizuno', 'mizuno running'],
        'salomon': ['salomon', 'salomon running'],
        'altra': ['altra', 'altra running'],
        'on': ['on', 'on running'],
    }

    # Suffixes to remove for matching (variants)
    VARIANT_SUFFIXES = [
        'tr', 'trail', 'gtx', 'gore-tex', 'goretex',
        'wide', 'narrow',
        'men', 'women', 'mens', 'womens',
        'homme', 'femme',
        'road', 'marathon',
        'edition', 'limited',
        'plus', 'premium',
    ]

    @staticmethod
    def normalize_name(name: str) -> str:
        """
        Normalize product name for matching

        Steps:
        1. Lowercase
        2. Remove special chars except spaces/hyphens
        3. Normalize whitespace
        4. Remove variant suffixes
        5. Sort words alphabetically (except brand/model core)

        Example:
            "Asics Gel-Nimbus 27 TR" -> "asics gel nimbus 27"
            "ASICS GEL NIMBUS 27" -> "asics gel nimbus 27"
        """
        # Step 1: Lowercase
        normalized = name.lower().strip()

        # Step 2: Remove special chars but keep spaces/hyphens
        normalized = re.sub(r'[^\w\s\-]', '', normalized)

        # Step 3: Replace hyphens with spaces, normalize whitespace
        normalized = re.sub(r'[-_]+', ' ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized)

        # Step 4: Remove variant suffixes
        words = normalized.split()
        filtered_words = []

        for word in words:
            # Skip if word is a variant suffix
            if word not in ProductMatcher.VARIANT_SUFFIXES:
                filtered_words.append(word)

        normalized = ' '.join(filtered_words)

        # Step 5: Remove common articles
        normalized = re.sub(r'\b(the|le|la|les|de|des)\b', '', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()

        return normalized

    @staticmethod
    def extract_brand(name: str) -> Optional[str]:
        """
        Extract brand from product name
        Returns normalized brand or None
        """
        name_lower = name.lower()

        for brand, variations in ProductMatcher.BRAND_VARIATIONS.items():
            for variation in variations:
                if name_lower.startswith(variation):
                    return brand

        # Fallback: first word is brand
        first_word = name_lower.split()[0] if name_lower else None
        return first_word

    @staticmethod
    def extract_model_core(name: str) -> str:
        """
        Extract model core name (without brand and version number)

        Example:
            "Nike Pegasus 41" -> "pegasus"
            "ASICS Gel Nimbus 27" -> "gel nimbus"
        """
        normalized = ProductMatcher.normalize_name(name)
        words = normalized.split()

        if not words:
            return ""

        # Remove brand (first word typically)
        brand = ProductMatcher.extract_brand(name)
        if brand and words[0] == brand:
            words = words[1:]

        # Remove version number (last word if numeric)
        if words and words[-1].replace('v', '').isdigit():
            words = words[:-1]

        return ' '.join(words)

    @staticmethod
    def similarity_score(name1: str, name2: str) -> float:
        """
        Calculate similarity score between two product names
        Returns float between 0.0 (no match) and 1.0 (exact match)
        """
        norm1 = ProductMatcher.normalize_name(name1)
        norm2 = ProductMatcher.normalize_name(name2)

        # Exact match
        if norm1 == norm2:
            return 1.0

        # Brand must match
        brand1 = ProductMatcher.extract_brand(name1)
        brand2 = ProductMatcher.extract_brand(name2)

        if brand1 != brand2:
            return 0.0  # Different brands = no match

        # Model core similarity
        model1 = ProductMatcher.extract_model_core(name1)
        model2 = ProductMatcher.extract_model_core(name2)

        # Use SequenceMatcher for fuzzy matching
        model_similarity = SequenceMatcher(None, model1, model2).ratio()

        # Version number matching (CRITICAL: penalize if versions differ)
        version1 = re.search(r'(\d+)(?:\.\d+)?$', ProductMatcher.normalize_name(name1))
        version2 = re.search(r'(\d+)(?:\.\d+)?$', ProductMatcher.normalize_name(name2))

        version_modifier = 0.0
        if version1 and version2:
            # Both have version numbers
            if version1.group(1) == version2.group(1):
                version_modifier = 0.2  # Bonus for matching versions
            else:
                version_modifier = -0.5  # PENALTY for different versions
        elif version1 or version2:
            # Only one has version number (partial match possible)
            version_modifier = -0.1

        final_score = max(0.0, min(1.0, model_similarity + version_modifier))
        return final_score

    @staticmethod
    def find_best_match(
        target_name: str,
        candidates: List[Dict],
        name_field: str = 'full_name',
        threshold: float = 0.75
    ) -> Optional[Dict]:
        """
        Find best matching product from list of candidates

        Args:
            target_name: Product name to match
            candidates: List of candidate products (dicts)
            name_field: Field name containing product name in candidates
            threshold: Minimum similarity score (0.0-1.0)

        Returns:
            Best matching candidate dict or None if no match above threshold
        """
        best_match = None
        best_score = 0.0

        for candidate in candidates:
            candidate_name = candidate.get(name_field, '')
            if not candidate_name:
                continue

            score = ProductMatcher.similarity_score(target_name, candidate_name)

            if score > best_score and score >= threshold:
                best_score = score
                best_match = candidate

        return best_match

    @staticmethod
    def create_match_report(matches: List[Dict]) -> str:
        """
        Create human-readable report of matches

        Args:
            matches: List of dicts with keys: irun_name, runrepeat_name, score

        Returns:
            Formatted string report
        """
        report = []
        report.append("=" * 80)
        report.append("📊 Product Matching Report")
        report.append("=" * 80)
        report.append(f"\nTotal matches: {len(matches)}")
        report.append("")

        # Sort by score descending
        sorted_matches = sorted(matches, key=lambda x: x.get('score', 0), reverse=True)

        for i, match in enumerate(sorted_matches, 1):
            irun = match.get('irun_name', 'N/A')
            runrepeat = match.get('runrepeat_name', 'N/A')
            score = match.get('score', 0.0)

            confidence = "✅ HIGH" if score >= 0.9 else "⚠️  MEDIUM" if score >= 0.75 else "❌ LOW"

            report.append(f"{i}. {confidence} (score: {score:.2f})")
            report.append(f"   i-run:     {irun}")
            report.append(f"   RunRepeat: {runrepeat}")
            report.append("")

        report.append("=" * 80)

        return "\n".join(report)


# Unit tests
if __name__ == '__main__':
    print("🧪 Testing ProductMatcher...\n")

    # Test cases
    test_cases = [
        ("Asics Gel-Nimbus 27 TR", "ASICS Gel Nimbus 27", True),
        ("Nike Pegasus 41", "Nike Air Zoom Pegasus 41", True),
        ("Brooks Glycerin GTS 22", "Brooks Glycerin 22 GTS", True),
        ("ASICS Novablast 5", "Asics Novablast 5", True),
        ("Hoka Bondi 9", "HOKA ONE ONE Bondi 9", True),
        ("Nike Pegasus 41", "Asics Gel-Nimbus 27", False),  # Different brands
        ("Brooks Ghost 16", "Brooks Ghost 15", False),  # Different versions
    ]

    print("Test 1: Normalization")
    print("-" * 60)
    for name, _, _ in test_cases[:5]:
        normalized = ProductMatcher.normalize_name(name)
        print(f"{name:40} → {normalized}")

    print("\n\nTest 2: Brand extraction")
    print("-" * 60)
    for name, _, _ in test_cases[:5]:
        brand = ProductMatcher.extract_brand(name)
        print(f"{name:40} → {brand}")

    print("\n\nTest 3: Model core extraction")
    print("-" * 60)
    for name, _, _ in test_cases[:5]:
        model = ProductMatcher.extract_model_core(name)
        print(f"{name:40} → {model}")

    print("\n\nTest 4: Similarity scoring")
    print("-" * 60)
    for name1, name2, should_match in test_cases:
        score = ProductMatcher.similarity_score(name1, name2)
        match_status = "✅ MATCH" if score >= 0.75 else "❌ NO MATCH"
        expected = "✅" if should_match else "❌"
        correct = "✅" if (score >= 0.75) == should_match else "❌ INCORRECT"

        print(f"{name1} vs {name2}")
        print(f"  Score: {score:.2f} | {match_status} | Expected: {expected} | {correct}")
        print()

    print("=" * 60)
    print("✅ ProductMatcher tests complete")
