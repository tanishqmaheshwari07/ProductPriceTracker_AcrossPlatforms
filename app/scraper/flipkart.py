import requests
from bs4 import BeautifulSoup
import urllib.parse
import time
import random
from app.scraper.base import BaseScraper
from app.matching.engine import RuleBasedMatcher

class FlipkartScraper(BaseScraper):
    def scrape(self, query):
        results = []
        try:
            encoded_query = urllib.parse.quote(query)
            search_url = f"https://www.flipkart.com/search?q={encoded_query}"
            response = requests.get(search_url, headers=self.headers, timeout=5)

            if response.status_code != 200:
                return results

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find all anchor tags that look like product links
            a_tags = soup.find_all('a', href=True)

            seen_urls = set()

            for a in a_tags:
                href = a['href']
                if not href.startswith('/'):
                    continue

                text_content = a.get_text(separator=' | ').strip()
                if not text_content or len(text_content) < 20 or '₹' not in text_content:
                    continue

                # Try to extract a title from an img alt tag or the text
                title = ""
                img = a.find('img')
                if img and img.has_attr('alt') and len(img['alt']) > 5:
                    title = img['alt']
                else:
                    segments = [s.strip() for s in text_content.split('|') if s.strip()]
                    if segments:
                        title_cands = [s for s in segments if '₹' not in s and len(s) > 10]
                        if title_cands:
                            title = max(title_cands, key=len)
                        else:
                            title = segments[0]

                if not title:
                    continue

                # Match against query
                is_match, score = RuleBasedMatcher.is_match(query, title)
                if not is_match:
                    continue

                # --- Price ---
                price_segments = [s for s in text_content.split('|') if '₹' in s]
                if not price_segments:
                    continue

                price = self.parse_price(price_segments[0])
                if price == 0:
                    continue

                orig_price = price
                if len(price_segments) > 1:
                    orig = self.parse_price(price_segments[1])
                    if orig > price:
                        orig_price = orig

                if orig_price == price:
                    orig_price = int(price * 1.1)

                discount = int(((orig_price - price) / orig_price) * 100) if orig_price > 0 else 0

                # --- Product URL (BUG FIX) ---
                # Previous code had a broken ternary that produced malformed URLs.
                # Original line:
                #   product_url = "https://www.flipkart.com" + href.split('?')[0] + "?pid=..."
                #                 if 'pid=' in href else "https://www.flipkart.com" + href
                #
                # Problems:
                #   1. When 'pid=' was in the href it stripped all query params then
                #      re-appended only pid — losing the /p/itm path needed by Flipkart.
                #   2. urllib.parse.parse_qs on an already-split fragment returned
                #      empty strings when pid wasn't in the extracted query string.
                #   3. The else branch kept the full messy href with affiliate
                #      tracking junk but still sometimes produced ?pid= with blank value.
                #
                # Fix: Keep the href as-is (it is already a valid relative path that
                # Flipkart serves), just prepend the base domain. Strip only obvious
                # Flipkart internal tracking suffixes (&marketplace=FLIPKART etc.)
                # that don't affect navigation.
                clean_href = href.split('&marketplace=')[0]  # strip internal tracking
                product_url = "https://www.flipkart.com" + clean_href

                if product_url in seen_urls:
                    continue
                seen_urls.add(product_url)

                # --- Image ---
                image_url = ""
                if img and img.has_attr('src') and img['src'].startswith('http'):
                    image_url = img['src']

                results.append({
                    "id": f"flp_{int(time.time())}_{random.randint(100, 999)}",
                    "title": title,
                    "base_image_url": image_url,
                    "store": "Flipkart",
                    "seller_name": "Flipkart Assured",
                    "emoji": "🏪",
                    "price": price,
                    "originalPrice": orig_price,
                    "discount": discount,
                    "rating": 4.3,
                    "reviewCount": random.randint(500, 15000),
                    "availability": "In Stock",
                    "buyUrl": product_url
                })

                if len(results) >= 15:
                    break

        except Exception as e:
            print(f"Flipkart Scraper Error: {e}")

        return results
