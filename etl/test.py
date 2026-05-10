"""Quick test: fetch CoinGecko data and print it (no GCS/BQ needed)."""
from main import fetch, transform

data = fetch()
rows = transform(data)

for c in rows[:5]:
    print(f"{c['symbol']:>6}  ${c['current_price']:<10}  {c['name']}")

print(f"\nTotal coins fetched: {len(rows)}")
