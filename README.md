# Uncle Joe's Coffee Shop API

## Project Overview
This backend powers the Uncle Joe’s Coffee Shop app. It connects to Google BigQuery and exposes an HTTP API that a frontend can call to show locations, menu items, member profiles, orders, search, and stats.

## What This API Does
- **Locations**: list and filter store locations, plus store‑level orders and stats
- **Menu**: list, filter, sort, and recommend menu items
- **Members + Orders**: login, profile lookup, order history, and loyalty points
- **Search + Stats**: search across locations and menu, plus analytics endpoints

## API Endpoints (Core Section)

### `GET /locations`
Lists store locations.  
Use case: store locator page and filtering.

Supports: `state`, `city`, `open_for_business`, `wifi`, `drive_thru`, `door_dash`, `limit`, `offset`.

### `GET /locations/{location_id}`
Returns one location by ID.  
Use case: store detail page.

### `GET /menu`
Lists menu items.  
Use case: menu page with filters and sorting.

Supports: `category`, `min_price`, `max_price`, `sort_by`, `sort_dir`, `limit`, `offset`.

### `GET /menu/{item_id}`
Returns one menu item by ID.  
Use case: menu item detail view.

## API Endpoints (Expanded)

These endpoints add richer functionality for a full‑feature frontend: authentication, member views, order history, analytics, and cross‑entity search.

### `POST /login`
Authenticates a Coffee Club member by email and password.  
Use case: login form for the member portal.

Behavior notes:
- Compares the submitted password against the bcrypt hash stored in BigQuery.
- Returns a small profile summary on success.

### `GET /members/{member_id}`
Returns a member profile (name, email, home store, etc.).  
Use case: account/profile page.

### `GET /members/{member_id}/orders`
Returns a member’s order history in reverse‑chronological order.  
Use case: “Past Orders” screen with optional line items.

Supports: `limit`, `offset`, `include_items`, `sort_by`, `sort_dir`.

### `GET /members/{member_id}/points`
Returns loyalty points, calculated as the sum of `floor(order_total)` across orders.  
Use case: rewards summary and points balance display.

### `GET /locations/{location_id}/orders`
Returns orders placed at a specific store.  
Use case: store performance view and staff dashboards.

Supports: `limit`, `offset`, `include_items`, `sort_by`, `sort_dir`.

### `GET /locations/{location_id}/stats`
Returns store‑level totals: total orders, total revenue, and average order value.  
Use case: store dashboard summary widget.

### `GET /locations/{location_id}/stats/daily`
Returns daily order totals for a store (date + totals).  
Use case: daily trend chart or ops reporting.

### `GET /locations/{location_id}/stats/weekly`
Returns weekly order totals for a store (week + totals).  
Use case: week‑over‑week trend chart.

### `GET /search`
Searches locations and menu items using a single query string.  
Use case: global search bar and “quick find.”

Supports: `scope=all|locations|menu`, `limit`.

### `GET /stats/orders`
Returns overall order stats for the entire business.  
Use case: admin dashboard and executive summary.

### `GET /stats/top-items`
Returns top‑selling menu items based on order history.  
Use case: merchandising, promo planning, and “top sellers” modules.

### `GET /stats/top-locations`
Returns top‑performing locations by revenue/orders.  
Use case: regional performance view.

### `GET /menu/recommendations`
Returns recommended menu items derived from order history.  
Use case: “popular items” and “seasonal favorites” sections.

Supports: `kind=all_time|seasonal`, `window_days`, `limit`.

### `GET /docs`
Interactive API documentation (Swagger UI).

### `GET /healthz` and `GET /readyz`
Health checks for uptime and BigQuery connectivity.

## Key Features
- BigQuery integration (real data, no mocks)
- Cloud Run ready
- CORS enabled for frontend use
- Swagger docs at `/docs`
- Filtering, pagination, sorting, search
- Store and global stats endpoints

## How to Run (Minimal)
1. Install dependencies: `poetry install`
2. Start the API: `poetry run uvicorn main:app --reload`

## How to Use the API
- Base URL: `http://127.0.0.1:8000`
- Open docs: `http://127.0.0.1:8000/docs`
- A frontend should call the endpoints above to fetch data for pages, search, and dashboards.
