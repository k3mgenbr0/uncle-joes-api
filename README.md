# Uncle Joe's Coffee Shop API

## Contributors

- [Colten Brandt](https://github.com/brandt10)
- 

## Project Overview
This backend powers the Uncle Joe’s Coffee Shop app. It connects to Google BigQuery and exposes an HTTP API that a frontend can call to show locations, menu items, member profiles, orders, search, and stats.

## What This API Does
- **Locations**: list and filter store locations, plus store‑level orders and stats
- **Menu**: list, filter, sort, and recommend menu items
- **Members + Orders**: login, profile lookup, order history, and loyalty points
- **Search + Stats**: search across locations and menu, plus analytics endpoints

Frontend-facing backend behaviors:
- session-based member auth with secure cookies
- pickup ordering with pay-at-store checkout
- store-aware ordering rules driven by `open_for_business`
- backend-provided store display labels and nearby-store metadata
- richer rewards metadata for tier progress and milestone UI
- pickup-time validation against store-local hours
- order progress fields for confirmation and history screens

## API Endpoints (Core Section)

### `GET /locations`
Lists store locations.  
Use case: store locator page and filtering.

Supports: `state`, `city`, `open_for_business`, `orderable_only`, `wifi`, `drive_thru`, `door_dash`, `limit`, `offset`.

Location responses now also include frontend-friendly store-selection fields:
- `display_name`
- `address`
- `nearby_store_ids`
- `region`
- `metro_area`

Availability notes:
- `open_for_business` is the single source of truth for whether a store can accept orders
- stores where `open_for_business !== true` return:
  - `ordering_available: false`
  - `availability_status: "coming_soon"`
  - `availability_message: "Coming Soon!"`
- use `orderable_only=true` for pickup-store dropdowns and other ordering UIs
- unavailable stores should still render on the location page, but must not be used for ordering

### `GET /locations/{location_id}`
Returns one location by ID.  
Use case: store detail page.

Includes address, coordinates, hours, `hours_today`, `open_now`, service flags, and derived store detail fields.

### `GET /locations/{location_id}/availability`
Returns a store-availability helper payload for ordering flows.  
Use case: smarter pickup messaging, disabling invalid checkout states, and showing the next open/close window.

Includes:
- `ordering_available`
- `open_now`
- `accepting_orders_now`
- `availability_status`
- `availability_message`
- `next_open_at`
- `next_close_at`
- `valid_pickup_windows`

### `GET /locations/nearby`
Returns locations sorted by distance from a `lat`/`lng` point.  
Use case: nearby-store suggestions, geolocation fallback pickup selection, and “closest open store” flows.

Supports: `lat`, `lng`, `limit`, `orderable_only`, `open_for_business`.

Nearby responses include:
- `distance_miles`
- `display_name`
- `address`
- `ordering_available`
- `availability_status`
- `availability_message`
- `nearby_store_ids`

### `GET /menu`
Lists menu items.  
Use case: menu page with filters and sorting.

Supports: `category`, `min_price`, `max_price`, `sort_by`, `sort_dir`, `limit`, `offset`.

### `GET /menu/{item_id}`
Returns one menu item by ID.  
Use case: menu item detail view.

Includes detail-friendly fields such as tags, availability status, nullable media/description fields, and related items.

## API Endpoints (Expanded)

These endpoints add richer functionality for a full‑feature frontend: authentication, member views, order history, analytics, and cross‑entity search.

### `POST /login`
Authenticates a Coffee Club member by email and password.  
Use case: login form for the member portal.

Behavior notes:
- Compares the submitted password against the bcrypt hash stored in BigQuery.
- Returns a small profile summary on success.

### `POST /api/member/login`
Starts a member session and sets a secure, HTTP‑only cookie.  
Use case: login for the member dashboard.

Cookie behavior for deployed frontend use:
- `HttpOnly`
- `Secure`
- `SameSite=None`
- `Path=/`

### `POST /api/member/logout`
Clears the member session cookie.  
Use case: log out of the dashboard.

### `GET /api/member/session`
Returns the currently authenticated member.  
Use case: keep the UI in sync with login state.

Session/profile responses now keep preferred-store data aligned by returning:
- `preferred_store_id`
- `preferred_store` summary with `location_id`, `store_name`, `display_name`, `city`, `state`, `full_address`, `address`, and `phone`

### `GET /api/member/profile`
Returns the authenticated member profile with derived rewards and preferred-store data.  
Use case: account settings and profile screen.

Profile/session data now exposes additive rewards fields such as:
- `current_points`
- `lifetime_points`
- `rewards_tier`
- `points_to_next_reward`
- `next_tier_name`
- `current_tier_min_points`
- `next_tier_min_points`
- `next_reward_threshold`
- `current_reward_progress`

### `GET /api/member/points`
Returns the authenticated member’s points balance.  
Use case: profile and rewards widgets.

### `GET /api/member/points/history`
Returns a per-order breakdown of points earned, newest first.  
Use case: rewards history section and “how did I earn these points?” views.

Supports: `limit`.

Each history entry includes:
- `order_id`
- `order_date`
- `store_id`
- `store_name`
- `store_city`
- `store_state`
- `order_total`
- `points_earned`
- `points_redeemed`
- `activity_type`

The response remains a list for backward compatibility, and empty histories return `[]`.

### `GET /api/member/rewards`
Returns a dedicated rewards summary for the authenticated member.  
Use case: tier progress bars, milestone cards, “next reward” messaging, and summary stats.

Guaranteed fields:
- `member_id`
- `current_points`
- `lifetime_points`
- `rewards_tier`
- `points_to_next_reward`
- `next_tier_name`
- `current_tier_min_points`
- `next_tier_min_points`
- `next_reward_threshold`
- `current_reward_progress`
- `points_earned_last_30_days`
- `points_earned_last_90_days`
- `bonus_programs`

### `GET /api/member/rewards/redemptions`
Returns the authenticated member’s rewards redemptions.  
Use case: “points spent” history and future redemption UX.

Current behavior:
- the endpoint is available now
- the dataset does not currently track real redemptions
- the response returns `redemptions: []` and `redemption_tracking_enabled: false`

### `GET /api/member/favorites`
Returns the authenticated member’s favorite menu items.  
Use case: profile and dashboard favorites section.

Includes:
- inferred favorites from purchase history
- explicit saved favorites added by the member

Supports: `limit`, `window_days`, `store_id`.

Favorites now include richer menu metadata to support reorder flows:
- `available_sizes`
- `default_size`
- `current_price`
- `image_url`

When `store_id` is provided, favorites also include store-aware fields:
- `available_at_store`
- `store_availability_status`

### `POST /api/member/favorites`
Saves an explicit favorite menu item for the authenticated member.  
Use case: “Save as favorite” buttons in menu and order history views.

### `DELETE /api/member/favorites/{menu_item_id}`
Removes an explicit favorite menu item for the authenticated member.  
Use case: “Unfavorite” actions in the profile area.

### `GET /api/member/orders`
Returns the authenticated member’s order history.  
Use case: account order history views.

### `POST /api/member/orders`
Creates a new pickup order for the authenticated member with `pay_in_store` checkout.  
Use case: cart submission and order confirmation for the customer app.

Behavior notes:
- validates the store and menu items before creating the order
- validates pickup time against the store’s posted hours in store-local time
- rejects pickup times outside the valid window with a precise message
- blocks ordering when `open_for_business !== true`
- computes subtotal, tax, total, and `points_earned`
- returns a full order detail payload ready for a confirmation screen

Order fields now include:
- `pickup_time`
- `ready_by_estimate`
- `submitted_at`
- `order_status`
- `estimated_prep_minutes`
- `special_instructions`
- nested location summary and store phone when available

Pickup validation notes:
- `pickup_time` should be sent as ISO 8601
- `pickup_time` is optional; if omitted, the backend accepts the order and computes a ready estimate automatically
- validation uses the selected store’s local business hours
- the backend returns precise errors such as:
  - `Pickup time must be between 5:30 AM and 8:00 PM for this store.`
  - `This store is closed on Monday.`
  - `This store is not yet open for ordering. Coming Soon!`

### `POST /api/member/orders/preview`
Returns a non-persisted order preview using the same validation rules as real checkout.  
Use case: cart review screens, pricing previews, pickup validation before submit, and “estimated points earned” UX.

Preview payloads include:
- pricing totals
- `ready_by_estimate`
- `points_earned`
- validated line items
- payment summary
- optional `warnings`

### `POST /api/member/orders/{order_id}/reorder`
Builds a preview from a past order using the authenticated member’s history.  
Use case: reorder buttons from favorites or order history without recreating the cart client-side.

Behavior notes:
- uses the same store/item validation rules as current ordering
- can accept optional overrides like `store_id`, `pickup_time`, and `special_instructions`
- returns an order-preview payload with `source_order_id`

### `GET /api/member/orders/{order_id}`
Returns one order for the authenticated member using the session-first member API.  
Use case: order confirmation and “view recent order” screens without member-id routing.

### `GET /api/member/summary`
Returns the authenticated member profile, points, recents, and favorites in one call.  
Use case: profile page hydration without member-id routing.

Supports: `include_items`, `recent_limit`, `favorites_limit`, `favorites_window_days`, `store_id`.

### `GET /api/member/dashboard`
Returns member profile, points balance, and orders with store info and line items.  
Use case: primary dashboard data fetch.

Supports: `include_items`, `limit`, `offset`, `store_id`.

Dashboard response also includes:
- `pagination` (limit/offset/total)
- `points_earned` per order
- `favorites`
- `points_history`
- `rewards`

Dashboard and order-history responses include order-progress fields such as:
- `pickup_time`
- `ready_by_estimate`
- `submitted_at`
- `order_status`
- `estimated_prep_minutes`
- `special_instructions`
- `store_phone`
- `items` as an array, even when empty

Order status values:
- `order_received`
- `brewing`
- `finishing_touches`
- `ready_for_pickup`
- `completed`
- `cancelled`

Order creation uses the configured `ORDER_TAX_RATE` environment variable, which defaults to `0.07`.

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

### `GET /members/{member_id}/recent`
Returns a member’s most recent orders (defaults to the last 5).  
Use case: “Recent activity” card on the account page.

Supports: `include_items`, `limit`.

### `GET /members/{member_id}/favorites`
Returns a member’s most‑ordered menu items.  
Use case: “Your favorites” section.

Supports: `limit`, `window_days`, `store_id`.

### `GET /members/{member_id}/favorites/trends`
Returns weekly trends for a member’s top items in a recent window.  
Use case: “Your favorites over time” chart.

Supports: `window_days`, `limit_items`.

### `GET /members/{member_id}/summary`
Returns a combined payload: profile, points, recent orders, and favorites.  
Use case: one request to hydrate the member dashboard.

Supports: `include_items`, `recent_limit`, `favorites_limit`, `favorites_window_days`, `store_id`.

### `GET /locations/{location_id}/orders`
Returns orders placed at a specific store.  
Use case: store performance view and staff dashboards.

Supports: `limit`, `offset`, `include_items`, `sort_by`, `sort_dir`.

### `GET /locations/{location_id}/menu`
Returns menu items annotated for a specific pickup location.  
Use case: store-aware ordering and pickup-store menu filtering.

Current availability behavior is static:
- if `open_for_business === true`, returned items are marked available
- otherwise, returned items are marked unavailable and the store should be treated as coming soon

Returned menu items may include:
- `available_at_store`
- `store_availability_status`

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

Supports: `scope=all|locations|menu`, `limit`, `fuzzy`, `min_score`, plus optional filters for locations and menu items.

Location filters: `location_state`, `location_city`, `location_open_for_business`, `location_wifi`, `location_drive_thru`, `location_door_dash`.  
Menu filters: `menu_category`, `menu_size`, `menu_min_price`, `menu_max_price`.

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

### `GET /menu/categories`
Returns the distinct list of menu categories.  
Use case: menu filter dropdown.

### `GET /menu/sizes`
Returns the distinct list of menu sizes.  
Use case: size filter chips.

### `GET /menu/{item_id}/stats`
Returns order stats for a single menu item (orders, quantity, revenue, last order date).  
Use case: item detail insights.

Supports: `window_days` for time‑bounded stats.

### `GET /orders/{order_id}`
Returns a full order detail payload for the authenticated member.  
Use case: dedicated order detail page.

### `GET /rewards/program`
Returns rewards-program metadata for the app.  
Use case: “How rewards work,” milestone explanations, and future promotions UI.

Program metadata includes:
- `points_rule`
- `tiers`
- `reward_thresholds`
- `bonus_programs`

Current tier thresholds are exposed directly by the backend so the frontend does not have to hardcode them.

### `GET /docs`
Interactive API documentation (Swagger UI).

### `GET /healthz` and `GET /readyz`
Health checks for uptime and BigQuery connectivity.

## Key Features
- BigQuery integration (real data, no mocks)
- Cloud Run ready
- CORS enabled for frontend use
- Cookie-based member sessions
- Pickup ordering with pay-in-store checkout
- Order preview and reorder flows for faster checkout UX
- Store availability enforcement from `open_for_business`
- Store availability helper payloads for pickup UX
- Nearby-store lookup with distance sorting
- Backend-provided `display_name` store labels for ordering UIs
- Explicit favorites write support
- Favorites enriched for reorder flows
- Dedicated rewards summary and rewards program metadata
- Pickup-time validation against store-local hours
- Swagger docs at `/docs`
- Filtering, pagination, sorting, fuzzy search
- Store and global stats endpoints

## How to Run (Minimal)
1. Install dependencies: `poetry install`
2. Start the API: `poetry run uvicorn main:app --reload`

Frontend/CORS notes:
- Local frontend origins for common dev servers are allowed by default: `localhost:3000`, `localhost:5173`, and `localhost:4173` (plus `127.0.0.1` equivalents).
- For deployed frontends, set `FRONTEND_URL` or `FRONTEND_URLS`.
- For session cookies across different origins, set `AUTH_COOKIE_SECURE=true` and `AUTH_COOKIE_SAMESITE=none` behind HTTPS.

## How to Use the API
- Base URL: `http://127.0.0.1:8000`
- Open docs: `http://127.0.0.1:8000/docs`
- A frontend should call the endpoints above to fetch data for pages, search, and dashboards.
- Member endpoints under `/api/member` set and read an HTTP‑only session cookie.
- Browser-based member requests should use `credentials: "include"` so the session cookie is sent.
