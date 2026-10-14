-- Event Services Marketplace: Postgres schema (Supabase-compatible)
-- Wishlists/boards intentionally left for a later version.

CREATE TABLE categories (
    id    SERIAL PRIMARY KEY,
    name  TEXT NOT NULL UNIQUE            -- e.g. DJ, Photographer, Caterer, Venue, Photo Booth
);

CREATE TABLE vendors (
    id           SERIAL PRIMARY KEY,
    name         TEXT NOT NULL,
    category_id  INT  NOT NULL REFERENCES categories(id),
    description  TEXT,
    city         TEXT NOT NULL,
    county       TEXT,
    email        TEXT,
    phone        TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE services (
    id           SERIAL PRIMARY KEY,
    vendor_id    INT  NOT NULL REFERENCES vendors(id) ON DELETE CASCADE,
    name         TEXT NOT NULL,
    description  TEXT,
    base_price   NUMERIC(10,2) NOT NULL CHECK (base_price >= 0),
    price_unit   TEXT NOT NULL CHECK (price_unit IN ('flat', 'per_hour', 'per_person', 'per_item')),
    min_guests   INT  CHECK (min_guests >= 0),
    max_guests   INT  CHECK (max_guests > 0),
    CHECK (max_guests IS NULL OR min_guests IS NULL OR max_guests >= min_guests)
);

CREATE TABLE availability (
    id         SERIAL PRIMARY KEY,
    vendor_id  INT  NOT NULL REFERENCES vendors(id) ON DELETE CASCADE,
    date       DATE NOT NULL,
    is_booked  BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (vendor_id, date)
);

CREATE TABLE clients (
    id          SERIAL PRIMARY KEY,
    first_name  TEXT NOT NULL,
    last_name   TEXT NOT NULL,
    email       TEXT NOT NULL UNIQUE,
    phone       TEXT
);

-- One planned event (a wedding, birthday, work party) that groups many bookings.
CREATE TABLE events (
    id           SERIAL PRIMARY KEY,
    client_id    INT  NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    name         TEXT NOT NULL,
    event_type   TEXT NOT NULL CHECK (event_type IN ('wedding', 'birthday', 'corporate', 'anniversary', 'graduation', 'other')),
    event_date   DATE NOT NULL,
    city         TEXT NOT NULL,
    county       TEXT,
    guest_count  INT  NOT NULL CHECK (guest_count > 0),
    budget       NUMERIC(10,2) CHECK (budget >= 0),
    status       TEXT NOT NULL DEFAULT 'planning' CHECK (status IN ('planning', 'booked', 'completed', 'cancelled')),
    notes        TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- One row = one service booked for one event.
-- The client, date, location, and guest count all come from the event.
CREATE TABLE bookings (
    id                 SERIAL PRIMARY KEY,
    event_id           INT  NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    service_id         INT  NOT NULL REFERENCES services(id),
    quantity           INT  NOT NULL DEFAULT 1 CHECK (quantity > 0),   -- hours, items, etc. (people use events.guest_count)
    agreed_price       NUMERIC(10,2) NOT NULL CHECK (agreed_price >= 0), -- total price for this booking
    status             TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'cancelled')),
    confirmation_code  TEXT UNIQUE,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE reviews (
    id          SERIAL PRIMARY KEY,
    client_id   INT NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    vendor_id   INT NOT NULL REFERENCES vendors(id) ON DELETE CASCADE,
    booking_id  INT UNIQUE REFERENCES bookings(id),  -- ties a review to a real booking (one review per booking)
    rating      INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment     TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------
-- Views: computed values so they never drift out of date
-- ---------------------------------------------------------------

-- Average rating per vendor (replaces a stored avg on vendors)
CREATE VIEW vendor_ratings AS
SELECT v.id AS vendor_id,
       ROUND(AVG(r.rating), 2) AS avg_rating,
       COUNT(r.id) AS review_count
FROM vendors v
LEFT JOIN reviews r ON r.vendor_id = v.id
GROUP BY v.id;

-- Budget tracking per event (cancelled bookings are ignored)
CREATE VIEW event_budget_summary AS
SELECT e.id AS event_id,
       e.name AS event_name,
       e.event_date,
       e.city,
       e.guest_count,
       e.budget,
       COALESCE(SUM(b.agreed_price) FILTER (WHERE b.status <> 'cancelled'), 0) AS total_cost,
       e.budget - COALESCE(SUM(b.agreed_price) FILTER (WHERE b.status <> 'cancelled'), 0) AS budget_remaining,
       (e.budget IS NULL
        OR COALESCE(SUM(b.agreed_price) FILTER (WHERE b.status <> 'cancelled'), 0) <= e.budget) AS within_budget
FROM events e
LEFT JOIN bookings b ON b.event_id = e.id
GROUP BY e.id;

-- ---------------------------------------------------------------
-- Column comments (also useful to include in the schema sent to the LLM)
-- ---------------------------------------------------------------
COMMENT ON COLUMN services.price_unit IS 'How base_price is charged: flat, per_hour, per_person, or per_item';
COMMENT ON COLUMN services.min_guests IS 'Smallest guest count this service supports (NULL = no minimum)';
COMMENT ON COLUMN services.max_guests IS 'Largest guest count this service supports; for venues this is capacity';
COMMENT ON COLUMN availability.is_booked IS 'TRUE if the vendor is unavailable on this date';
COMMENT ON COLUMN events.budget IS 'Client''s total budget for the whole event (NULL = no budget set)';
COMMENT ON COLUMN bookings.agreed_price IS 'Total agreed price for this booking (already includes quantity)';
COMMENT ON COLUMN bookings.quantity IS 'Number of hours or items booked; not used for per_person pricing';
COMMENT ON VIEW event_budget_summary IS 'Per event: total cost of non-cancelled bookings, budget remaining, and whether it is within budget';