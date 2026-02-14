PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS properties (
  id INTEGER PRIMARY KEY,
  source TEXT,
  source_property_id TEXT,
  address TEXT,
  city TEXT,
  state TEXT,
  zip TEXT,
  lat REAL,
  lon REAL,
  beds REAL,
  baths REAL,
  sqft INTEGER,
  year_built INTEGER,
  lot_size REAL,
  property_type TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  UNIQUE(source, source_property_id)
);

CREATE TABLE IF NOT EXISTS listings (
  id INTEGER PRIMARY KEY,
  property_id INTEGER NOT NULL,
  source TEXT,
  source_listing_id TEXT,
  status TEXT,
  list_price REAL,
  list_date TEXT,
  last_seen TEXT,
  url TEXT,
  psf REAL,
  days_on_market INTEGER,
  created_at TEXT DEFAULT (datetime('now')),
  UNIQUE(source, source_listing_id),
  FOREIGN KEY(property_id) REFERENCES properties(id)
);

CREATE TABLE IF NOT EXISTS sales (
  id INTEGER PRIMARY KEY,
  property_id INTEGER NOT NULL,
  source TEXT,
  sale_price REAL,
  sale_date TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY(property_id) REFERENCES properties(id)
);

CREATE TABLE IF NOT EXISTS media (
  id INTEGER PRIMARY KEY,
  listing_id INTEGER NOT NULL,
  url TEXT,
  sha256 TEXT,
  condition_score REAL,
  labels_json TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY(listing_id) REFERENCES listings(id)
);

CREATE TABLE IF NOT EXISTS comp_sets (
  id INTEGER PRIMARY KEY,
  listing_id INTEGER NOT NULL,
  median_psf REAL,
  comp_count INTEGER,
  radius_miles REAL,
  sqft_band_pct REAL,
  created_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY(listing_id) REFERENCES listings(id)
);

CREATE TABLE IF NOT EXISTS underwrites (
  id INTEGER PRIMARY KEY,
  listing_id INTEGER NOT NULL,
  arv REAL,
  discount_pct REAL,
  condition_score REAL,
  rehab_cost REAL,
  score REAL,
  reasons_json TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY(listing_id) REFERENCES listings(id)
);

CREATE TABLE IF NOT EXISTS alerts (
  id INTEGER PRIMARY KEY,
  listing_id INTEGER NOT NULL,
  channel TEXT,
  to_address TEXT,
  sent_at TEXT,
  payload_json TEXT,
  FOREIGN KEY(listing_id) REFERENCES listings(id)
);

CREATE TABLE IF NOT EXISTS ingest_runs (
  id INTEGER PRIMARY KEY,
  source TEXT,
  started_at TEXT,
  ended_at TEXT,
  new_listings INTEGER,
  updated_listings INTEGER,
  errors_json TEXT
);
