import concurrent.futures
import urllib.parse
import random
from app.scraper.amazon import AmazonScraper
from app.scraper.flipkart import FlipkartScraper
from app.mock_data import PRODUCT_DATA


class ScraperManager:

    @staticmethod
    def get_fallback_data(query, existing_stores, anchor_price=None):
        """
        Generate fallback entries for stores we couldn't scrape due to bot-protection.

        BUG FIX: Previous code used a Google search URL
        (https://www.google.com/search?q=buy+...) as the buyUrl for Croma and
        Reliance Digital, meaning clicking "Buy" sent users to Google, not to the
        actual retailer.

        Fix: Use the real search-result pages of each retailer so the link at least
        lands on the correct store's search results for the query, which is the best
        we can do without scraping those sites.
        """
        results = []
        encoded_q = urllib.parse.quote(query)

        # Map store → their real search URL template
        STORE_SEARCH_URLS = {
            'Croma':            f"https://www.croma.com/searchB?q={encoded_q}",
            'Reliance Digital': f"https://www.reliancedigital.in/search?q={encoded_q}:relevance",
            'Apple Store':      f"https://www.apple.com/in/search/{encoded_q}",
        }

        for item in PRODUCT_DATA:
            if item['store'] in existing_stores:
                continue

            new_item = dict(item)
            new_item['title'] = query.title()

            base_price = anchor_price if anchor_price else item['price']
            price_variance = random.uniform(0.95, 1.05)
            new_item['price'] = int(base_price * price_variance)
            new_item['originalPrice'] = int(new_item['price'] * 1.15)
            new_item['discount'] = int(
                ((new_item['originalPrice'] - new_item['price']) / new_item['originalPrice']) * 100
            )
            new_item['seller_name'] = f"{item['store']} Official Seller"
            new_item['base_image_url'] = (
                "https://via.placeholder.com/300x300?text=" + urllib.parse.quote(query)
            )

            store_name = new_item['store']
            # Use actual retailer search pages instead of Google
            new_item['buyUrl'] = STORE_SEARCH_URLS.get(
                store_name,
                f"https://www.google.com/search?q=buy+{encoded_q}+{urllib.parse.quote(store_name)}"
            )

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
                if amz_results:
                    results.extend(amz_results)
            except Exception as e:
                print("Amazon scrape failed or timed out:", e)

            try:
                flp_results = future_flp.result(timeout=10)
                if flp_results:
                    results.extend(flp_results)
            except Exception as e:
                print("Flipkart scrape failed or timed out:", e)

        # Existing stores found
        existing_stores = {r['store'] for r in results}

        # Calculate anchor price from scraped results
        anchor_price = None
        valid_prices = [r['price'] for r in results if r.get('price')]
        if valid_prices:
            anchor_price = sum(valid_prices) / len(valid_prices)

        # Add fallback for missing stores (Croma, Reliance, etc.)
        results.extend(ScraperManager.get_fallback_data(query, existing_stores, anchor_price))

        return results
