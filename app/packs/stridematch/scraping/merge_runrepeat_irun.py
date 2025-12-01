"""
Data fusion script: merge RunRepeat lab data + i-run e-commerce data
Produces complete dataset ready for PostgreSQL import

Input files:
  - runrepeat_data.csv: Complete lab specs (stack, cushioning, energy return)
  - irun_data.csv: E-commerce data (descriptions, prices, images)

Output:
  - merged_shoes_data.csv: Complete dataset with 100% schema coverage
"""

import csv
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from product_matcher import ProductMatcher


class DataMerger:
    """Merge product data from multiple sources"""

    # Expected columns from RunRepeat
    RUNREPEAT_COLUMNS = [
        'full_name', 'brand', 'release_year', 'category', 'url',
        'drop_mm', 'stack_heel_mm', 'stack_forefoot_mm',
        'cushioning_softness_ha', 'energy_return_pct',
        'weight_g', 'weight_size_reference',
        'median_lifespan_km', 'outsole_durability',
        'midsole_material', 'stability_type', 'recommended_use', 'price_usd'
    ]

    # Expected columns from i-run
    IRUN_COLUMNS = [
        'full_name', 'brand', 'description', 'price_eur',
        'image_url', 'product_url',
        'drop_mm', 'weight_g', 'stability_type', 'recommended_use'
    ]

    # Output columns (complete schema)
    OUTPUT_COLUMNS = [
        'full_name', 'brand', 'release_year', 'category',
        'description', 'price_eur', 'price_usd',
        'image_url', 'product_url_irun', 'product_url_runrepeat',
        'drop_mm', 'stack_heel_mm', 'stack_forefoot_mm',
        'cushioning_softness_ha', 'energy_return_pct',
        'weight_g', 'weight_size_reference',
        'median_lifespan_km', 'outsole_durability',
        'midsole_material', 'stability_type', 'recommended_use',
        'source', 'match_score', 'merged_at'
    ]

    def __init__(self):
        self.matcher = ProductMatcher()

    def load_csv(self, filepath: str) -> List[Dict]:
        """Load CSV file into list of dicts"""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        data = []
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)

        return data

    def merge_product(
        self,
        runrepeat: Dict,
        irun: Optional[Dict] = None,
        match_score: float = 0.0
    ) -> Dict:
        """
        Merge RunRepeat + i-run data for a single product

        Priority:
          - Lab data (stack, cushioning, energy): RunRepeat ONLY (authoritative)
          - Drop, weight: RunRepeat preferred, i-run fallback
          - Description, price EUR, images: i-run ONLY
          - URLs: both sources preserved
        """
        merged = {}

        # Product identity (RunRepeat is primary)
        merged['full_name'] = runrepeat.get('full_name', '')
        merged['brand'] = runrepeat.get('brand', '')
        merged['release_year'] = runrepeat.get('release_year', '')
        merged['category'] = runrepeat.get('category', 'Road Running')

        # Lab specs (RunRepeat ONLY - authoritative source)
        merged['drop_mm'] = runrepeat.get('drop_mm', '')
        merged['stack_heel_mm'] = runrepeat.get('stack_heel_mm', '')
        merged['stack_forefoot_mm'] = runrepeat.get('stack_forefoot_mm', '')
        merged['cushioning_softness_ha'] = runrepeat.get('cushioning_softness_ha', '')
        merged['energy_return_pct'] = runrepeat.get('energy_return_pct', '')
        merged['weight_g'] = runrepeat.get('weight_g', '')
        merged['weight_size_reference'] = runrepeat.get('weight_size_reference', 'US 9')
        merged['median_lifespan_km'] = runrepeat.get('median_lifespan_km', '')
        merged['outsole_durability'] = runrepeat.get('outsole_durability', '')
        merged['midsole_material'] = runrepeat.get('midsole_material', '')
        merged['stability_type'] = runrepeat.get('stability_type', '')
        merged['recommended_use'] = runrepeat.get('recommended_use', '')

        # Pricing
        merged['price_usd'] = runrepeat.get('price_usd', '')
        merged['price_eur'] = ''

        # URLs
        merged['product_url_runrepeat'] = runrepeat.get('url', '')
        merged['product_url_irun'] = ''

        # E-commerce data (i-run only)
        merged['description'] = ''
        merged['image_url'] = ''

        # If i-run data is available, enrich
        if irun:
            merged['description'] = irun.get('description', '')
            merged['price_eur'] = irun.get('price_eur', '')
            merged['image_url'] = irun.get('image_url', '')
            merged['product_url_irun'] = irun.get('product_url', '')

            # Fallback values (only if RunRepeat doesn't have them)
            if not merged['drop_mm']:
                merged['drop_mm'] = irun.get('drop_mm', '')
            if not merged['weight_g']:
                merged['weight_g'] = irun.get('weight_g', '')
            if not merged['stability_type']:
                merged['stability_type'] = irun.get('stability_type', '')

        # Metadata
        merged['source'] = 'runrepeat+irun' if irun else 'runrepeat_only'
        merged['match_score'] = f"{match_score:.2f}" if irun else 'N/A'
        merged['merged_at'] = datetime.utcnow().isoformat()

        return merged

    def merge_datasets(
        self,
        runrepeat_path: str,
        irun_path: Optional[str] = None,
        output_path: str = 'merged_shoes_data.csv',
        match_threshold: float = 0.75
    ) -> Dict:
        """
        Merge RunRepeat + i-run datasets

        Returns:
            Dict with stats: {
                'total_products': int,
                'matched': int,
                'unmatched': int,
                'match_rate': float
            }
        """
        print("=" * 80)
        print("🔄 Data Fusion: RunRepeat + i-run")
        print("=" * 80)

        # Load RunRepeat data (primary source)
        print(f"\n📥 Loading RunRepeat data from: {runrepeat_path}")
        runrepeat_data = self.load_csv(runrepeat_path)
        print(f"   Loaded {len(runrepeat_data)} products from RunRepeat")

        # Load i-run data if available
        irun_data = []
        if irun_path:
            print(f"\n📥 Loading i-run data from: {irun_path}")
            irun_data = self.load_csv(irun_path)
            print(f"   Loaded {len(irun_data)} products from i-run")
        else:
            print("\n⚠️  No i-run data provided (RunRepeat only mode)")

        # Merge products
        print("\n🔗 Matching products across sources...")
        merged_products = []
        match_report = []

        for runrepeat_product in runrepeat_data:
            runrepeat_name = runrepeat_product.get('full_name', '')

            if not runrepeat_name:
                print(f"   ⚠️  Skipping product with missing name")
                continue

            # Try to find matching i-run product
            irun_match = None
            match_score = 0.0

            if irun_data:
                irun_match = self.matcher.find_best_match(
                    target_name=runrepeat_name,
                    candidates=irun_data,
                    name_field='full_name',
                    threshold=match_threshold
                )

                if irun_match:
                    irun_name = irun_match.get('full_name', '')
                    match_score = self.matcher.similarity_score(runrepeat_name, irun_name)

                    match_report.append({
                        'runrepeat_name': runrepeat_name,
                        'irun_name': irun_name,
                        'score': match_score
                    })

                    print(f"   ✅ MATCH: {runrepeat_name} ↔ {irun_name} (score: {match_score:.2f})")
                else:
                    print(f"   ❌ NO MATCH: {runrepeat_name}")

            # Merge data
            merged = self.merge_product(
                runrepeat=runrepeat_product,
                irun=irun_match,
                match_score=match_score
            )
            merged_products.append(merged)

        # Write output CSV
        print(f"\n💾 Writing merged data to: {output_path}")
        output_file = Path(output_path)

        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.OUTPUT_COLUMNS)
            writer.writeheader()
            writer.writerows(merged_products)

        # Calculate stats
        matched_count = len([p for p in merged_products if p['source'] == 'runrepeat+irun'])
        unmatched_count = len([p for p in merged_products if p['source'] == 'runrepeat_only'])
        match_rate = (matched_count / len(merged_products) * 100) if merged_products else 0

        stats = {
            'total_products': len(merged_products),
            'matched': matched_count,
            'unmatched': unmatched_count,
            'match_rate': match_rate
        }

        # Print summary
        print("\n" + "=" * 80)
        print("✅ Data Fusion Complete")
        print("=" * 80)
        print(f"\n📊 Statistics:")
        print(f"   Total products: {stats['total_products']}")
        print(f"   Matched (RunRepeat + i-run): {stats['matched']}")
        print(f"   Unmatched (RunRepeat only): {stats['unmatched']}")
        print(f"   Match rate: {stats['match_rate']:.1f}%")
        print(f"\n💾 Output file: {output_file.absolute()}")

        # Generate match report if matches exist
        if match_report:
            print("\n" + self.matcher.create_match_report(match_report))

        return stats


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Merge RunRepeat lab data + i-run e-commerce data'
    )
    parser.add_argument(
        '--runrepeat',
        required=True,
        help='Path to RunRepeat CSV file'
    )
    parser.add_argument(
        '--irun',
        default=None,
        help='Path to i-run CSV file (optional)'
    )
    parser.add_argument(
        '--output',
        default='merged_shoes_data.csv',
        help='Output CSV file path'
    )
    parser.add_argument(
        '--threshold',
        type=float,
        default=0.75,
        help='Minimum similarity score for matching (0.0-1.0)'
    )

    args = parser.parse_args()

    merger = DataMerger()
    stats = merger.merge_datasets(
        runrepeat_path=args.runrepeat,
        irun_path=args.irun,
        output_path=args.output,
        match_threshold=args.threshold
    )

    print(f"\n✅ Merge completed successfully")
    print(f"   {stats['matched']} products matched with i-run data")
    print(f"   {stats['unmatched']} products from RunRepeat only")


if __name__ == '__main__':
    main()
