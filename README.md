# Crypto ETL Pipeline

Serverless batch ETL pipeline using Cloud Run Functions. Fetches cryptocurrency market data from CoinGecko and loads it into BigQuery.

## Architecture

```
Cloud Scheduler (every hour)
        │
        ▼
┌─────────────────────────────────────┐
│  Cloud Function: crypto-pipeline     │
│  (HTTP-triggered, gen2)             │
│                                     │
│  1. Fetch from CoinGecko API        │
│  2. Write CSV to GCS bucket         │
│  3. Load CSV into BigQuery          │
└─────────────────────────────────────┘
```

## Project Structure

```
07-gcp-etl/
├── etl/
│   ├── main.py              # Cloud Function entry point
│   ├── test.py              # Local test (no cloud resources needed)
│   ├── requirements.txt     # Python dependencies
│   └── .gcloudignore
├── Justfile                 # just setup / deploy / trigger / test / undeploy
└── README.md
```

## Prerequisites

- [just](https://github.com/casey/just#installation)
- Google Cloud SDK
- Python 3.11

## Setup

```sh
git clone ...
cd 07-gcp-etl
just setup
```

This creates:

- GCS bucket: `gs://project-bf17aaec-fbc3-4e62-a95-crypto-etl`
- BigQuery dataset: `crypto_data`
- Service account: `crypto-pipeline-sa` with minimal permissions (`bigquery.user`, `bigquery.dataEditor`, `storage.objectCreator`)

## Deploy

```sh
just deploy
```

This deploys:

- Cloud Function `crypto-pipeline` (HTTP-triggered, gen2, asia-southeast1)
- Cloud Scheduler job `crypto-hourly` (runs every hour)

## Usage

| Command         | Description                             |
| --------------- | --------------------------------------- |
| `just setup`    | Create bucket, dataset, service account |
| `just deploy`   | Deploy function + create scheduler      |
| `just trigger`  | Manually invoke the function            |
| `just test`     | Fetch data locally (no cloud needed)    |
| `just undeploy` | Delete function + scheduler             |

## API

Source: [CoinGecko API](https://www.coingecko.com/en/api) — free, no API key required for basic public endpoints.

## IAM

The dedicated service account `crypto-pipeline-sa` has only the permissions it needs:

| Role                          | Purpose                          |
| ----------------------------- | -------------------------------- |
| `roles/bigquery.user`         | Run BigQuery jobs                |
| `roles/bigquery.dataEditor`   | Write data to tables             |
| `roles/storage.objectCreator` | Upload CSV files to GCS          |
| `roles/storage.objectViewer`  | Read CSV files for BigQuery load |
