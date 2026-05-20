from app.ml.product_matcher import ProductMatcher
from app.ml.recommendation_engine import RecommendationEngine

def group_by_product_variant(raw_results, query):
    if not raw_results:
        return []
        
    variants = []
    matcher = ProductMatcher()
    
    for item in raw_results:
        # Try to find an existing variant that matches this one closely
        matched_variant = None
        best_match_info = None
        
        for variant in variants:
            match_result = matcher.match(item['title'], variant['product_title'])
            if match_result["matched"]:
                matched_variant = variant
                best_match_info = match_result
                break
                
        if not matched_variant:
            # Create new variant group
            matched_variant = {
                "product_title": item['title'],
                "base_image_url": item.get('base_image_url', ''),
                "platforms": {},
                "_raw_items": [],
                "match_confidence": 100.0, # Self match is 100%
                "match_quality": "strong",
                "match_type": "exact"
            }
            variants.append(matched_variant)
        else:
            # Keep the lowest confidence score as the overall group confidence if it's lower, 
            # or you can just store the latest match info. We'll store it if we don't have one,
            # or average it, but let's just keep the worst case or the first match.
            # Actually, let's keep the best_match_info for the group to display on UI.
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
            # Sort by price ascending
            items.sort(key=lambda x: x['price'])
            
            cheapest = items[0]
            
            # Backlog of all sellers for this store
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
            
        # Optional: pick absolute best image from cheapest item across all stores if base_image_url is empty
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
        
    return results
