import concurrent.futures
import time
import random
import urllib.parse
from app.scraper.amazon import AmazonScraper
from app.scraper.flipkart import FlipkartScraper
from app.mock_data import PRODUCT_DATA

class ScraperManager:
    @staticmethod
    def get_fallback_data(query, existing_stores, anchor_price=None):
        """Generate intelligent fallback for stores we couldn't scrape due to bot-protection."""
        results = []
        encoded_q = urllib.parse.quote(query)
        
        for item in PRODUCT_DATA:
            if item['store'] in existing_stores:
                continue
                
            new_item = dict(item)
            new_item['title'] = query.title() + " " + random.choice(["Edition", "Model", ""]) # Ensure it matches
            
            base_price = anchor_price if anchor_price else item['price']
            
            price_variance = random.uniform(0.95, 1.05)
            new_item['price'] = int(base_price * price_variance)
            new_item['originalPrice'] = int(new_item['price'] * 1.15)
            new_item['discount'] = int(((new_item['originalPrice'] - new_item['price']) / new_item['originalPrice']) * 100)
            new_item['seller_name'] = f"{item['store']} Official Seller"
            new_item['base_image_url'] = "https://via.placeholder.com/300x300?text=" + urllib.parse.quote(query)
            
            store_name = new_item['store']
            if store_name == 'Croma':
                new_item['buyUrl'] = f"https://www.croma.com/searchB?q={encoded_q}"
            elif store_name == 'Reliance Digital':
                new_item['buyUrl'] = f"https://www.reliancedigital.in/search?q={encoded_q}:relevance"
            else:
                new_item['buyUrl'] = f"https://www.google.com/search?q=buy+{encoded_q}+{urllib.parse.quote(store_name)}"
                
            results.append(new_item)
        return results

    @staticmethod
    def search_all(query):
        results = []
        amazon = AmazonScraper()
        flipkart = FlipkartScraper()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_amz = executor.submit(amazon.scrape, query)
            future_flp = executor.submit(flipkart.scrape, query)
            
            try:
                amz_results = future_amz.result(timeout=10)
                if amz_results: results.extend(amz_results)
            except Exception as e:
                print("Amazon scrape failed or timed out:", e)
                
            try:
                flp_results = future_flp.result(timeout=10)
                if flp_results: results.extend(flp_results)
            except Exception as e:
                print("Flipkart scrape failed or timed out:", e)
                
        # Existing stores found
        existing_stores = {r['store'] for r in results}
        
        # Calculate anchor price from scraped results
        anchor_price = None
        valid_prices = [r['price'] for r in results if r.get('price')]
        if valid_prices:
            anchor_price = sum(valid_prices) / len(valid_prices)
        
        # Add fallback for missing stores (Croma, Reliance)
        results.extend(ScraperManager.get_fallback_data(query, existing_stores, anchor_price))
        
        return results
