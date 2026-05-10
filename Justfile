project := "project-bf17aaec-fbc3-4e62-a95"
bucket := "project-bf17aaec-fbc3-4e62-a95-crypto-etl"
dataset := "crypto_data"
location := "asia-southeast1"
sa := "crypto-pipeline-sa@" + project + ".iam.gserviceaccount.com"

setup:
	gcloud storage buckets create gs://{{bucket}} --location={{location}} || true
	gcloud alpha bq datasets create --project={{project}} {{dataset}} || true
	gcloud iam service-accounts create crypto-pipeline-sa --display-name="Crypto Pipeline SA" || true
	gcloud projects add-iam-policy-binding {{project}} --member="serviceAccount:{{sa}}" --role=roles/bigquery.user
	gcloud projects add-iam-policy-binding {{project}} --member="serviceAccount:{{sa}}" --role=roles/bigquery.dataEditor
	gcloud projects add-iam-policy-binding {{project}} --member="serviceAccount:{{sa}}" --role=roles/storage.objectCreator
	gcloud projects add-iam-policy-binding {{project}} --member="serviceAccount:{{sa}}" --role=roles/storage.objectViewer

deploy:
	gcloud functions deploy crypto-pipeline \
	  --gen2 --runtime=python311 --region={{location}} \
	  --source=etl --entry-point=extract --trigger-http \
	  --no-allow-unauthenticated \
	  --service-account={{sa}} \
	  --set-env-vars=PROJECT_ID={{project}},BUCKET_NAME={{bucket}},BQ_DATASET={{dataset}}
	gcloud scheduler jobs create http crypto-hourly \
	  --location={{location}} --schedule="0 * * * *" \
	  --uri=$(gcloud functions describe crypto-pipeline --gen2 --region={{location}} --format="value(serviceConfig.uri)") \
	  --oidc-service-account-email={{sa}} || true

undeploy:
	gcloud scheduler jobs delete crypto-hourly --location={{location}} --quiet || true
	gcloud functions delete crypto-pipeline --region={{location}} --gen2 --quiet || true

trigger:
	gcloud functions call crypto-pipeline --region={{location}} --gen2

test:
	cd etl && python test.py

all: setup deploy
