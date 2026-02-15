import requests
from bs4 import BeautifulSoup
import time
import json
import random
import re
import os

def get_article_links(index_url, max_pages=100):
    """
    Crawls the blog pagination to find article links.
    """
    links = set()
    page = 1
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    print(f"🔍 [Scraper] Collecting links from {index_url}...")

    while page <= max_pages:
        # Construct pagination URL
        if page == 1:
            url = index_url
        else:
            url = f"{index_url.rstrip('/')}/page/{page}/"

        try:
            print(f"   ⏳ Checking Page {page}...", end="\r")
            resp = requests.get(url, headers=headers, timeout=15)
            
            # If 404, we have gone past the last page
            if resp.status_code == 404:
                print(f"\n   🏁 Reached end of blog at Page {page}. Stopping.")
                break
            
            if resp.status_code != 200:
                print(f"\n   ⚠️ Page {page} returned {resp.status_code}. Skipping.")
                page += 1
                continue

            soup = BeautifulSoup(resp.text, 'html.parser')
            
            new_links_found = 0
            for a in soup.find_all('a', href=True):
                href = a['href']
                
                # Filter for years (2020-2029 or 2010-2019) to find blog posts
                # This regex looks for /YYYY/MM/ pattern common in WordPress
                if re.search(r'/\d{4}/\d{2}/', href):
                    if href not in links:
                        links.add(href)
                        new_links_found += 1
            
            print(f"   ✅ Page {page}: Found {new_links_found} new articles. (Total: {len(links)})")
            
            # If we load a valid page but find 0 new article links, we are likely on a 
            # widget page or archive that isn't the main loop. Best to stop.
            if new_links_found == 0 and page > 1:
                print("   🏁 No new article links found on this page. Stopping.")
                break

            page += 1
            # Sleep to prevent blocking
            time.sleep(random.uniform(1, 2))

        except Exception as e:
            print(f"\n   ❌ Error on page {page}: {e}")
            break

    return list(links)

def scrape_article_content(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return None

        soup = BeautifulSoup(resp.text, 'html.parser')

        # 1. Get Title
        title_tag = soup.find('h1')
        title = title_tag.get_text(strip=True) if title_tag else "No Title"
        
        # 2. Get Date
        date_meta = soup.find('meta', property='article:published_time')
        date = date_meta['content'] if date_meta else ""

        # 3. Get Content
        article_body = soup.find(class_='entry-content') or \
                       soup.find(class_='post-content') or \
                       soup.find('article') or \
                       soup.find('main')
        
        if article_body:
            # Optional: Remove "Share this" buttons if present
            for junk in article_body.find_all(class_='sharedaddy'):
                junk.decompose()
            content = article_body.get_text(separator="\n", strip=True)
        else:
            content = ""

        return {
            "title": title,
            "link": url,
            "date": date,
            "content": content
        }

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    blog_index_url = "https://apnswami.wordpress.com/blogpages" 
    
    # 1. Collect Links (INCREASED MAX_PAGES TO 100)
    article_urls = get_article_links(blog_index_url, max_pages=100)
    
    print(f"\n🚀 Starting scrape of {len(article_urls)} articles...")
    
    # Check if file exists to load previous progress (Optional, simple overwrite here)
    scraped_data = []
    
    # 2. Scrape & Save Incrementally
    for i, link in enumerate(article_urls):
        print(f"   [{i+1}/{len(article_urls)}] Scraping: {link}")
        
        data = scrape_article_content(link)
        if data:
            scraped_data.append(data)
        
        # Save every 10 articles (so you don't lose data if it crashes)
        if (i + 1) % 10 == 0:
            with open("scraped_articles_partial.json", "w", encoding="utf-8") as f:
                json.dump(scraped_data, f, ensure_ascii=False, indent=4)
            print("      💾 (Auto-saved progress)")
            
        time.sleep(1) 

    # 3. Final Save
    with open("scraped_articles_final.json", "w", encoding="utf-8") as f:
        json.dump(scraped_data, f, ensure_ascii=False, indent=4)

    print(f"\n✅ DONE! Saved {len(scraped_data)} articles to 'scraped_articles_final.json'.")