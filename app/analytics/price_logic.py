from app.ml.product_matcher import ProductMatcher
from app.ml.recommendation_engine import RecommendationEngine


def group_by_product_variant(raw_results, query):
    if not raw_results:
        return []

    variants = []
    matcher = ProductMatcher()

    for item in raw_results:
        matched_variant = None
        best_match_info = None

        for variant in variants:
            match_result = matcher.match(item['title'], variant['product_title'])
            if match_result["matched"]:
                matched_variant = variant
                best_match_info = match_result
                break

        if not matched_variant:
            matched_variant = {
                "product_title": item['title'],
                "base_image_url": item.get('base_image_url', ''),
                "platforms": {},
                "_raw_items": [],
                "match_confidence": 100.0,
                "match_quality": "strong",
                "match_type": "exact"
            }
            variants.append(matched_variant)
        else:
            matched_variant["match_confidence"] = best_match_info["confidence"]
            matched_variant["match_quality"] = best_match_info["quality"]
            matched_variant["match_type"] = best_match_info["match_type"]

        matched_variant['_raw_items'].append(item)

    results = []

    for variant in variants:
        # Group raw items by store
        store_items = {}
        for item in variant['_raw_items']:
            store = item['store'].lower()
            if store not in store_items:
                store_items[store] = []
            store_items[store].append(item)

        platforms = {}

        for store, items in store_items.items():
            # Sort by price ascending — cheapest first
            items.sort(key=lambda x: x['price'])
            cheapest = items[0]

            backlog = []
            for itm in items:
                backlog.append({
                    "seller_name": itm.get('seller_name', 'Unknown Seller'),
                    "price": itm['price'],
                    "link": itm['buyUrl']
                })

            platforms[store] = {
                "cheapest_seller_name": cheapest.get('seller_name', 'Unknown Seller'),
                "lowest_price": cheapest['price'],
                "direct_seller_link": cheapest['buyUrl'],
                "all_sellers_backlog": backlog
            }

        # Pick best image from cheapest item across all stores if base_image_url is empty
        if not variant['base_image_url']:
            for item in variant['_raw_items']:
                if item.get('base_image_url'):
                    variant['base_image_url'] = item['base_image_url']
                    break

        results.append({
            "product_title": variant['product_title'],
            "base_image_url": variant['base_image_url'],
            "platforms": platforms,
            "match_confidence": variant.get("match_confidence", 100.0),
            "match_quality": variant.get("match_quality", "strong"),
            "match_type": variant.get("match_type", "exact")
        })

    return results


def process_scraped_data(raw_results, query="", trend_data=None):
    results = group_by_product_variant(raw_results, query)

    # Run recommendation engine on each variant's platforms
    for variant in results:
        best_platform = RecommendationEngine.rank_platforms(variant['platforms'], trend_data)
        variant['best_platform'] = best_platform

    # BUG FIX: Sort final results so the cheapest product variant appears first.
    # Previously the results were returned in whatever order the scraper returned them,
    # meaning the lowest-priced product was NOT guaranteed to be at the top of the list.
    # We sort by the absolute minimum price across all platforms for each variant.
    def get_min_price(variant):
        prices = [p['lowest_price'] for p in variant['platforms'].values() if p.get('lowest_price')]
        return min(prices) if prices else float('inf')

    results.sort(key=get_min_price)

    return results
