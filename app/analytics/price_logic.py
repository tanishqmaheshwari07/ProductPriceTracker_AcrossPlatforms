def process_scraped_data(raw_results):
    """
    Groups results by website, selects the lowest price per website,
    and identifies the overall best deal.
    """
    if not raw_results:
        return []
        
    store_groups = {}
    
    # 1. Group by Store
    for item in raw_results:
        store = item['store']
        if store not in store_groups:
            store_groups[store] = []
        store_groups[store].append(item)
        
    final_results = []
    
    # 2. Pick lowest price per store
    for store, items in store_groups.items():
        # Sort by price ascending
        items.sort(key=lambda x: x['price'])
        
        # Select the lowest price item for this store
        lowest_item = items[0]
        # Reset any leftover flags
        lowest_item['isBestDeal'] = False 
        
        # Initialize missing fields required by frontend
        if 'badges' not in lowest_item:
            lowest_item['badges'] = []
        if 'trend' not in lowest_item:
            lowest_item['trend'] = 'trend-up'
        if 'trendText' not in lowest_item:
            lowest_item['trendText'] = 'Stable'
        if 'delivery' not in lowest_item:
            lowest_item['delivery'] = 'Free Delivery'
            
        final_results.append(lowest_item)
        
    # 3. Pick the absolute lowest price across all stores to be the Best Deal
    if final_results:
        best_deal = min(final_results, key=lambda x: x['price'])
        best_deal['isBestDeal'] = True
        if 'best-deal' not in best_deal['badges']:
            best_deal['badges'].append('best-deal')
            
    return final_results

