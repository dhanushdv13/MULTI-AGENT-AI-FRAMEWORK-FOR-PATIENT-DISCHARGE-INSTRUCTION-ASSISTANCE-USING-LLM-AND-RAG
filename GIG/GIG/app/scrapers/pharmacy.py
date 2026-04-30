"""
Pharmacy Price Scraper - Multi-platform medicine price comparison
Scrapes 1mg, Apollo, and PharmEasy for medicine prices
"""
import re
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlencode
from typing import List, Dict, Optional

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0 Safari/537.36"
    )
}

PRICE_RE = re.compile(r"₹\s*[\d,]+(?:\.\d+)?")


def extract_first_price(text: str) -> Optional[str]:
    """Extract the first price from text."""
    m = PRICE_RE.search(text.replace("\xa0", " "))
    return m.group(0) if m else None


# ---------- Tata 1mg ----------

def search_1mg(query: str, limit: int = 5) -> List[Dict]:
    """
    Scrape Tata 1mg search results for medicine prices.
    """
    base_url = "https://www.1mg.com/search/all"
    url = f"{base_url}?{urlencode({'name': query})}"
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        results = []
        seen = set()

        # Heuristic: product links usually contain /drugs/ or /otc/
        for a in soup.select("a[href]"):
            href = a["href"]
            if not any(p in href for p in ("/drugs/", "/otc/")):
                continue

            name = a.get_text(strip=True)
            if not name or name in seen:
                continue

            card = a.find_parent("div")
            if not card:
                continue

            price = extract_first_price(card.get_text(" ", strip=True)) or "N/A"
            full_url = href if href.startswith("http") else f"https://www.1mg.com{href}"

            results.append({
                "source": "Tata 1mg",
                "name": name,
                "price": price,
                "url": full_url,
            })
            seen.add(name)

            if len(results) >= limit:
                break

        return results
        
    except Exception as e:
        print(f"[1mg] error: {e}")
        return []


# ---------- Apollo Pharmacy ----------

def search_apollo(query: str, limit: int = 5) -> List[Dict]:
    """
    Scrape Apollo Pharmacy search results.
    """
    base_url = "https://www.apollopharmacy.in/search-medicines"
    url = f"{base_url}?{urlencode({'q': query})}"
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        results = []
        seen = set()

        # Heuristic: medicine detail links generally contain /medicine/
        for a in soup.select("a[href]"):
            href = a["href"]
            if "/medicine/" not in href and "/otc/" not in href:
                continue

            name = a.get_text(strip=True)
            if not name or name in seen:
                continue

            card = a.find_parent("div")
            if not card:
                continue

            price = extract_first_price(card.get_text(" ", strip=True)) or "N/A"
            full_url = href if href.startswith("http") else f"https://www.apollopharmacy.in{href}"

            results.append({
                "source": "Apollo",
                "name": name,
                "price": price,
                "url": full_url,
            })
            seen.add(name)

            if len(results) >= limit:
                break

        return results
        
    except Exception as e:
        print(f"[Apollo] error: {e}")
        return []


# ---------- PharmEasy ----------

def search_pharmeasy(query: str, limit: int = 5) -> List[Dict]:
    """
    Scrape PharmEasy search results.
    """
    base_url = "https://pharmeasy.in/search/all"
    url = f"{base_url}?{urlencode({'name': query})}"
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        results = []
        seen = set()

        # Heuristic: medicine detail links contain /online-medicine-order/
        for a in soup.select("a[href]"):
            href = a["href"]
            if "/online-medicine-order/" not in href and "/otc/" not in href:
                continue

            name = a.get_text(strip=True)
            if not name or name in seen:
                continue

            card = a.find_parent("div")
            if not card:
                continue

            price = extract_first_price(card.get_text(" ", strip=True)) or "N/A"
            full_url = href if href.startswith("http") else f"https://pharmeasy.in{href}"

            results.append({
                "source": "PharmEasy",
                "name": name,
                "price": price,
                "url": full_url,
            })
            seen.add(name)

            if len(results) >= limit:
                break

        return results
        
    except Exception as e:
        print(f"[PharmEasy] error: {e}")
        return []


# ---------- Coordinator / "Swarm" ----------

AGENTS = {
    "tata_1mg": search_1mg,
    "apollo": search_apollo,
    "pharmeasy": search_pharmeasy,
}


def compare_prices(query: str, limit_per_source: int = 5) -> List[Dict]:
    """
    Search all pharmacy platforms in parallel and return combined results.
    
    Args:
        query: Medicine name to search
        limit_per_source: Maximum results per platform
        
    Returns:
        List of medicine results with name, price, source, and URL
    """
    results = []

    with ThreadPoolExecutor(max_workers=len(AGENTS)) as executor:
        futures = {
            executor.submit(fn, query, limit_per_source): name
            for name, fn in AGENTS.items()
        }

        for fut in as_completed(futures):
            name = futures[fut]
            try:
                data = fut.result()
                results.extend(data)
            except Exception as e:
                print(f"[{name}] error:", e)

    return results


def get_best_price(results: List[Dict]) -> Optional[Dict]:
    """Find the cheapest medicine from results."""
    if not results:
        return None
    
    # Filter out N/A prices and convert to float
    valid_results = []
    for r in results:
        price_str = r.get("price", "N/A")
        if price_str != "N/A":
            try:
                # Extract numeric value from price string
                price_num = float(re.sub(r'[^\d.]', '', price_str))
                valid_results.append({
                    **r,
                    "price_numeric": price_num
                })
            except (ValueError, AttributeError):
                continue
    
    if not valid_results:
        return None
    
    # Sort by price and return cheapest
    valid_results.sort(key=lambda x: x["price_numeric"])
    return valid_results[0]


def get_medicine_prices_tool(medicine_name: str) -> str:
    """
    Tool function that returns formatted price comparison results.
    Used by the Medicine Price Agent.
    """
    results = compare_prices(medicine_name, limit_per_source=5)
    
    if not results:
        return f"No results found for '{medicine_name}'. Try checking the spelling or using the generic name."
    
    # Format results
    output = [f"Price comparison for: {medicine_name}\n"]
    
    # Group by source
    by_source = {}
    for r in results:
        source = r['source']
        if source not in by_source:
            by_source[source] = []
        by_source[source].append(r)
    
    for source, items in by_source.items():
        output.append(f"\n{source}:")
        for item in items:
            output.append(f"  - {item['name']}: {item['price']}")
            output.append(f"    Link: {item['url']}")
    
    # Add best price
    best = get_best_price(results)
    if best:
        output.append(f"\nBest Price: {best['price']} at {best['source']}")
        output.append(f"Link: {best['url']}")
    
    return "\n".join(output)


if __name__ == "__main__":
    # Test the scraper
    q = input("Enter medicine name: ").strip() or "paracetamol 500"
    items = compare_prices(q)
    print(f"\nFound {len(items)} results:")
    for item in items:
        print(f"[{item['source']}] {item['name']} -> {item['price']} | {item['url']}")
    
    best = get_best_price(items)
    if best:
        print(f"\n✅ Best Price: {best['price']} at {best['source']}")
