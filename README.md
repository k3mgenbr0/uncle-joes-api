# Uncle Joe's Coffee Shop API

FastAPI backend for Uncle Joe's Coffee Shop. The API serves location and menu data directly from BigQuery and is structured for future frontend integration.

## Endpoints

- `GET /locations`
- `GET /locations/{location_id}`
- `GET /menu`
- `GET /menu/{item_id}`
- `GET /healthz`
- `GET /readyz`
- `GET /docs`

## Configuration

Required environment variables:

- `BQ_PROJECT_ID` or `GOOGLE_CLOUD_PROJECT`

Recommended environment variables:

- `BQ_DATASET` default: `uncle_joes`
- `BQ_LOCATIONS_TABLE` full table ID override, for example `my-project.coffee.locations`
- `BQ_MENU_TABLE` full table ID override, for example `my-project.coffee.menu`
- `CORS_ALLOW_ORIGINS` comma-separated list of allowed origins

Optional column-mapping environment variables are supported when your BigQuery schema differs from the defaults. The defaults assume:

- Locations: `location_id`, `name`, `address`, `city`, `state`, `postal_code`, `phone`, `hours`
- Menu: `item_id`, `name`, `category`, `description`, `price`, `currency`, `is_available`

## Local Development

1. Create and activate a virtual environment.
2. Install the app and dev tools:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

3. Export environment variables:

```bash
export BQ_PROJECT_ID="your-gcp-project"
export BQ_DATASET="uncle_joes"
export BQ_LOCATIONS_TABLE="your-gcp-project.uncle_joes.locations"
export BQ_MENU_TABLE="your-gcp-project.uncle_joes.menu"
export CORS_ALLOW_ORIGINS="http://localhost:5173,http://127.0.0.1:5173"
```

4. Run the API:

```bash
uvicorn app.main:app --reload
```

5. Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

## Tests

```bash
pytest
```

## Cloud Run Deployment

Build the container locally if you want to verify the image:

```bash
docker build -t uncle-joes-api .
docker run --rm -p 8080:8080 \
  -e BQ_PROJECT_ID="your-gcp-project" \
  -e BQ_LOCATIONS_TABLE="your-gcp-project.uncle_joes.locations" \
  -e BQ_MENU_TABLE="your-gcp-project.uncle_joes.menu" \
  uncle-joes-api
```

Deploy to Cloud Run:

```bash
gcloud run deploy uncle-joes-api \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars BQ_PROJECT_ID=your-gcp-project,BQ_LOCATIONS_TABLE=your-gcp-project.uncle_joes.locations,BQ_MENU_TABLE=your-gcp-project.uncle_joes.menu,CORS_ALLOW_ORIGINS=https://your-frontend-domain.com
```

If your service account does not already have access, grant BigQuery read permissions to the Cloud Run runtime identity before deploying.
