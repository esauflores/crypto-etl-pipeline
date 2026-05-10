import os
import json
import csv
import io
from datetime import datetime, timezone
import requests
from google.cloud import storage, bigquery

PROJECT_ID = os.environ.get("PROJECT_ID")
BUCKET_NAME = os.environ.get("BUCKET_NAME")
BQ_DATASET = os.environ.get("BQ_DATASET", "crypto_data")
BQ_TABLE = "market_data"

API_URL = "https://api.coingecko.com/api/v3/coins/markets"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CloudFunction/1.0)"}
PARAMS = {
    "vs_currency": "usd",
    "order": "market_cap_desc",
    "per_page": 100,
    "page": 1,
    "sparkline": "false",
}


def fetch():
    resp = requests.get(API_URL, params=PARAMS, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json()


def transform(data):
    return [{
        "id": c.get("id"),
        "symbol": c.get("symbol"),
        "name": c.get("name"),
        "current_price": c.get("current_price"),
        "market_cap": c.get("market_cap"),
        "market_cap_rank": c.get("market_cap_rank"),
        "total_volume": c.get("total_volume"),
        "price_change_24h": c.get("price_change_24h"),
        "price_change_percentage_24h": c.get("price_change_percentage_24h"),
        "circulating_supply": c.get("circulating_supply"),
        "total_supply": c.get("total_supply"),
        "ath": c.get("ath"),
        "ath_date": c.get("ath_date"),
    } for c in data]


def upload_to_gcs(rows):
    client = storage.Client(project=PROJECT_ID)
    bucket = client.bucket(BUCKET_NAME)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"crypto/market_data_{ts}.csv"

    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=rows[0].keys())
    w.writeheader()
    w.writerows(rows)

    bucket.blob(filename).upload_from_string(out.getvalue(), content_type="text/csv")
    return filename


def load_to_bigquery(gcs_uri):
    client = bigquery.Client(project=PROJECT_ID)
    table_id = f"{PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE}"
    job = client.load_table_from_uri(
        gcs_uri, table_id,
        job_config=bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.CSV,
            skip_leading_rows=1,
            autodetect=True,
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        ),
    )
    job.result()
    return client.get_table(table_id).num_rows


def extract(request):
    try:
        data = fetch()
        rows = transform(data)
        filename = upload_to_gcs(rows)
        gcs_uri = f"gs://{BUCKET_NAME}/{filename}"

        total_rows = load_to_bigquery(gcs_uri)

        return (json.dumps({
            "status": "ok",
            "records": len(rows),
            "file": gcs_uri,
            "bq_table": f"{PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE}",
            "total_rows": total_rows,
        }), 200, {"Content-Type": "application/json"})

    except Exception as e:
        return (json.dumps({
            "status": "error",
            "message": str(e),
        }), 500, {"Content-Type": "application/json"})
