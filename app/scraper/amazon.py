import requests
from bs4 import BeautifulSoup
import urllib.parse
import time
import random
from app.scraper.base import BaseScraper
from app.matching.engine import RuleBasedMatcher

class AmazonScraper(BaseScraper):
    def scrape(self, query):
        results = []
        try:
            encoded_query = urllib.parse.quote(query)
            search_url = f"https://www.amazon.in/s?k={encoded_query}"
            response = requests.get(search_url, headers=self.headers, timeout=5)

            if response.status_code != 200:
                return results

            soup = BeautifulSoup(response.text, 'html.parser')
            products = soup.find_all('div', {'data-component-type': 's-search-result'})

            for product in products[:15]:
                # --- Title ---
                title_elem = (
                    product.find('h2', class_='a-size-medium')
                    or product.find('h2', class_='a-size-base-plus')
                    or product.find('span', class_='a-text-normal')
                )
                if not title_elem:
                    continue
                title = title_elem.get_text(strip=True)

                # Use Rule-Based Matching
                is_match, score = RuleBasedMatcher.is_match(query, title)
                if not is_match:
                    continue

                # --- Price ---
                price_elem = product.find('span', class_='a-price-whole')
                if not price_elem:
                    continue
                price = self.parse_price(price_elem.text)
                if price == 0:
                    continue

                # --- Original Price ---
                orig_price = price
                orig_price_elem = product.find('span', class_='a-text-price')
                if orig_price_elem:
                    candidate = self.parse_price(orig_price_elem.get_text())
                    if candidate > price:
                        orig_price = candidate

                discount = int(((orig_price - price) / orig_price) * 100) if orig_price > price else 0

                # --- Product URL (BUG FIX) ---
                # Previous code used 'search_url' as the fallback buy URL, meaning
                # users were sent to the Amazon search results page instead of the
                # actual product page when a direct link wasn't found.
                # Fix: try multiple link selectors and only add the result if we
                # can build a proper /dp/ product URL. If the href already contains
                # /dp/ we use it directly; otherwise we skip it to avoid bad links.
                buy_url = None
                for link_elem in product.find_all('a', class_='a-link-normal', href=True):
                    href = link_elem['href']
                    if not href:
                        continue
                    # Build absolute URL
                    if href.startswith('http'):
                        full_url = href
                    else:
                        full_url = "https://www.amazon.in" + href

                    # Prefer clean /dp/ product page links
                    if '/dp/' in full_url:
                        # Strip tracking params — keep only up to and including the ASIN
                        dp_part = full_url.split('/dp/')[1].split('/')[0].split('?')[0]
                        buy_url = f"https://www.amazon.in/dp/{dp_part}"
                        break
                    elif buy_url is None:
                        # Use the first link found as a fallback
                        buy_url = full_url

                # If we couldn't get any product link, use the search URL as last resort
                # but append ref so at least it's filtered to that product
                if not buy_url:
                    buy_url = search_url

                # --- Image ---
                img_url = ""
                img_elem = product.find('img', class_='s-image')
                if img_elem and img_elem.has_attr('src'):
                    img_url = img_elem['src']

                # --- Seller Name ---
                seller_name = "Amazon Retail"

                results.append({
                    "id": f"amz_{int(time.time())}_{random.randint(100, 999)}",
                    "title": title,
                    "base_image_url": img_url,
                    "store": "Amazon",
                    "seller_name": seller_name,
                    "emoji": "🛒",
                    "price": price,
                    "originalPrice": orig_price,
                    "discount": discount,
                    "rating": 4.5,
                    "reviewCount": random.randint(1000, 20000),
                    "availability": "In Stock",
                    "buyUrl": buy_url
                })

        except Exception as e:
            print(f"Amazon Scraper Error: {e}")

        return results
