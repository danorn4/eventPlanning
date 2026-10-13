"""Fills the event marketplace database with fake (but realistic) Utah data.

WARNING: wipes all rows in the 8 tables first, so it is safe to re-run.
All vendors, clients, and reviews are made up.
Uses DATABASE_URL_ADMIN from .env.
"""
import os
import random
import string
from datetime import date, timedelta

import psycopg
from dotenv import load_dotenv

load_dotenv()
random.seed(42)  # same data every run

TODAY = date(2026, 10, 12)

CATEGORIES = ["DJ", "Photographer", "Caterer", "Venue", "Photo Booth", "Florist", "Videographer"]

COUNTY = {
    "Provo": "Utah", "Orem": "Utah", "Lehi": "Utah", "American Fork": "Utah",
    "Springville": "Utah", "Spanish Fork": "Utah",
    "Salt Lake City": "Salt Lake", "Sandy": "Salt Lake", "Draper": "Salt Lake",
    "Park City": "Summit", "Heber City": "Wasatch", "Ogden": "Weber",
    "Logan": "Cache", "St. George": "Washington",
}
CITIES = list(COUNTY)

# (category, name, city)
VENDORS = [
    ("DJ", "Wasatch Beats DJ Co.", "Provo"),
    ("DJ", "Silver Peak Sound", "Lehi"),
    ("DJ", "Beehive Beats", "Salt Lake City"),
    ("DJ", "Red Rock Rhythm", "St. George"),
    ("DJ", "Alpine Groove Entertainment", "Orem"),
    ("Photographer", "Golden Hour Studio", "Provo"),
    ("Photographer", "Timpanogos Lens Photography", "American Fork"),
    ("Photographer", "Summit Light Photography", "Park City"),
    ("Photographer", "Saltflat Portraits", "Salt Lake City"),
    ("Photographer", "Canyon Frame Photo", "Ogden"),
    ("Caterer", "Peach Pit Catering", "Springville"),
    ("Caterer", "Mountain Table Catering", "Draper"),
    ("Caterer", "Sego Lily Kitchen", "Salt Lake City"),
    ("Caterer", "Cache Valley Feasts", "Logan"),
    ("Caterer", "Desert Spoon Catering", "St. George"),
    ("Venue", "The Aspen Barn", "Heber City"),
    ("Venue", "Vineyard Hall at Lehi", "Lehi"),
    ("Venue", "Temple View Gardens", "Provo"),
    ("Venue", "Silver Lake Lodge", "Park City"),
    ("Venue", "Junction City Ballroom", "Ogden"),
    ("Venue", "The Brickyard Loft", "Salt Lake City"),
    ("Photo Booth", "Snap Happy Booths", "Orem"),
    ("Photo Booth", "Flash Mob Photo Booth", "Sandy"),
    ("Photo Booth", "Click & Giggle Booths", "Lehi"),
    ("Photo Booth", "Red Rock Booth Co.", "St. George"),
    ("Photo Booth", "Frame & Fun Booths", "Ogden"),
    ("Florist", "Bluebird Blooms", "Provo"),
    ("Florist", "Wildflower & Sage", "Salt Lake City"),
    ("Florist", "Petal Pushers of Park City", "Park City"),
    ("Florist", "Rosewood Floral Studio", "Logan"),
    ("Florist", "Marigold Lane Flowers", "Spanish Fork"),
    ("Videographer", "Northstar Films", "Salt Lake City"),
    ("Videographer", "Kindled Moments Video", "Orem"),
    ("Videographer", "Peak Frame Cinematics", "Park City"),
    ("Videographer", "Sunset Reel Co.", "St. George"),
    ("Videographer", "Evergreen Wedding Films", "Provo"),
]

DESCRIPTIONS = {
    "DJ": ["High-energy dance floor specialists for weddings and parties.",
           "Clean, crowd-reading sets with pro sound and lighting.",
           "Music for every generation, from first dance to last song."],
    "Photographer": ["Natural, candid storytelling photography.",
                     "Bright, timeless portraits and full-day event coverage.",
                     "Documentary-style photos that capture the real moments."],
    "Caterer": ["Locally sourced menus made from scratch.",
                "Flexible plated, buffet, and family-style service.",
                "Comfort-food classics with an elevated twist."],
    "Venue": ["A beautiful setting with room for ceremony and reception.",
              "Rustic charm with modern amenities and on-site coordination.",
              "Elegant indoor and outdoor spaces with mountain views."],
    "Photo Booth": ["Fun, prop-filled booths with instant prints and digital sharing.",
                    "Open-air booths that fit any group size.",
                    "Custom-branded photo strips and backdrops."],
    "Florist": ["Seasonal arrangements with a wild, garden-style look.",
                "Custom bouquets and florals designed around your colors.",
                "Locally grown blooms and creative installations."],
    "Videographer": ["Cinematic films that tell your whole story.",
                     "Highlight reels delivered fast, with drone footage available.",
                     "Story-driven wedding and event films."],
}

# (name, description, low price, high price, price_unit, min_guests, max_guests)
SERVICE_TEMPLATES = {
    "DJ": [
        ("DJ package - 4 hours", "DJ, sound system, and dance lighting for 4 hours.", 600, 1600, "flat", None, None),
        ("Additional hours", "Extend your DJ package beyond 4 hours.", 75, 200, "per_hour", None, None),
        ("Ceremony sound & wireless mic", "Speakers and mics for the ceremony.", 150, 400, "flat", None, None),
    ],
    "Photographer": [
        ("Wedding coverage - 8 hours", "Full-day coverage with edited online gallery.", 1800, 5000, "flat", None, None),
        ("Event photography - hourly", "Hourly coverage for parties and corporate events.", 150, 400, "per_hour", None, None),
        ("Engagement session", "One-hour session with 30+ edited photos.", 300, 800, "flat", None, None),
    ],
    "Caterer": [
        ("Plated dinner", "Three-course plated dinner with service staff.", 32, 75, "per_person", 30, 250),
        ("Buffet dinner", "Two-entree buffet with sides and salad.", 22, 55, "per_person", 40, 350),
        ("Dessert table", "Assorted desserts and a coffee station.", 350, 1200, "flat", 25, 250),
    ],
    "Venue": [
        ("Venue rental - full day", "Exclusive use of the venue for up to 10 hours.", 2500, 9000, "flat", None, None),
        ("Ceremony space add-on", "Dedicated ceremony area with chairs and setup.", 400, 1500, "flat", None, None),
        ("Tables & chairs package", "Tables, chairs, and linens for your guests.", 3, 10, "per_person", None, None),
    ],
    "Photo Booth": [
        ("Open-air photo booth - 3 hours", "Booth, attendant, props, and digital gallery.", 450, 1100, "flat", None, None),
        ("Additional booth hour", "Extend your booth rental.", 75, 200, "per_hour", None, None),
        ("Custom backdrop & props upgrade", "Themed backdrop and premium props.", 75, 250, "flat", None, None),
    ],
    "Florist": [
        ("Bridal bouquet", "Custom hand-tied bridal bouquet.", 85, 250, "per_item", None, None),
        ("Table centerpieces", "Seasonal centerpieces for each table.", 35, 120, "per_item", None, None),
        ("Ceremony arch florals", "Full floral installation for the ceremony arch.", 350, 1400, "flat", None, None),
    ],
    "Videographer": [
        ("Highlight film", "3 to 5 minute cinematic highlight film.", 1200, 3500, "flat", None, None),
        ("Full-day coverage", "All-day coverage with a full-length edit.", 2500, 6000, "flat", None, None),
        ("Drone footage add-on", "Aerial footage included in your film.", 250, 700, "flat", None, None),
    ],
}

STEP = {"flat": 25, "per_hour": 5, "per_person": 1, "per_item": 1}

FIRST = ["Emma", "Liam", "Olivia", "Noah", "Ava", "Ethan", "Sophia", "Mason",
         "Isabella", "Lucas", "Mia", "Jacob", "Chloe", "Caleb", "Hannah", "Tyler"]
LAST = ["Anderson", "Bennett", "Christensen", "Dalton", "Ellis", "Fowler", "Gardner",
        "Hansen", "Ingram", "Jensen", "Kimball", "Larsen", "Mitchell", "Nelson", "Olsen", "Peterson"]

EVENT_TYPES = ["wedding", "birthday", "corporate", "anniversary", "graduation", "other"]
EVENT_WEIGHTS = [9, 5, 4, 2, 1, 1]
GUESTS = {"wedding": (60, 250), "birthday": (20, 80), "corporate": (40, 200),
          "anniversary": (30, 100), "graduation": (25, 90), "other": (20, 100)}

COMMENTS = {
    5: ["Absolutely fantastic. Everyone raved about them.", "Professional, on time, and worth every penny.",
        "Made our day stress-free. Highly recommend!"],
    4: ["Great experience overall, just a few small hiccups.", "Very good service and friendly to work with.",
        "Would book again."],
    3: ["It was fine, but communication could have been better.", "Decent value, nothing special."],
    2: ["Arrived late and seemed rushed.", "Not quite what we expected for the price."],
}

N_EVENTS = 24
N_COMPLETED = 7


def rnd(x, step):
    return round(round(x / step) * step, 2)


def fits(s, guests):
    return ((s["min_guests"] is None or s["min_guests"] <= guests)
            and (s["max_guests"] is None or guests <= s["max_guests"]))


def random_weekend(start, end):
    while True:
        d = start + timedelta(days=random.randint(0, (end - start).days))
        if d.weekday() in (4, 5):  # Friday or Saturday
            return d


def build_data():
    categories = [{"id": i + 1, "name": n} for i, n in enumerate(CATEGORIES)]
    cat_id = {c["name"]: c["id"] for c in categories}

    # Vendors and services
    vendors, services = [], []
    desc_count = {}
    for i, (cat, name, city) in enumerate(VENDORS, start=1):
        k = desc_count.get(cat, 0)
        desc_count[cat] = k + 1
        desc = DESCRIPTIONS[cat][k % 3] + f" Serving {COUNTY[city]} County and beyond."
        slug = "".join(ch for ch in name.lower() if ch.isalnum())
        vendors.append({
            "id": i, "name": name, "category": cat, "category_id": cat_id[cat],
            "description": desc, "city": city, "county": COUNTY[city],
            "email": f"hello@{slug}.example.com",
            "phone": f"801-555-{random.randint(1000, 9999)}",
        })
        templates = SERVICE_TEMPLATES[cat]
        chosen = [templates[0]] + random.sample(templates[1:], random.randint(1, 2))
        if cat == "Venue":
            cap = random.choice([80, 120, 150, 200, 250, 300])
            vmin = random.choice([20, 30, 40, 50])
        for (sname, sdesc, lo, hi, unit, mn, mx) in chosen:
            if cat == "Venue":
                mn, mx = vmin, cap
            services.append({
                "id": len(services) + 1, "vendor_id": i, "name": sname, "description": sdesc,
                "base_price": rnd(random.uniform(lo, hi), STEP[unit]),
                "price_unit": unit, "min_guests": mn, "max_guests": mx,
            })
    by_vendor = {}
    for s in services:
        by_vendor.setdefault(s["vendor_id"], []).append(s)

    # Clients
    clients = []
    for i in range(16):
        clients.append({
            "id": i + 1, "first_name": FIRST[i], "last_name": LAST[i],
            "email": f"{FIRST[i].lower()}.{LAST[i].lower()}@example.com",
            "phone": f"385-555-{random.randint(1000, 9999)}",
        })

    # Events and bookings
    events, bookings = [], []
    busy = set()
    used_codes = set()

    def try_book(ev, cat, status):
        g = ev["guest_count"]
        pool_all = [v for v in vendors if v["category"] == cat]
        same = [v for v in pool_all if v["county"] == ev["county"]]
        pool = list(same if same and random.random() < 0.7 else pool_all)
        random.shuffle(pool)
        pool += [v for v in pool_all if v not in pool]
        for v in pool:
            if (v["id"], ev["event_date"]) in busy:
                continue
            options = [s for s in by_vendor[v["id"]] if fits(s, g)]
            if not options:
                continue
            s = random.choice(options)
            unit = s["price_unit"]
            if unit == "per_person":
                qty, total = 1, s["base_price"] * g
            elif unit == "per_hour":
                qty = random.randint(2, 5)
                total = s["base_price"] * qty
            elif unit == "per_item":
                qty = random.randint(1, 6) if "bouquet" in s["name"].lower() else random.randint(4, 12)
                total = s["base_price"] * qty
            else:
                qty, total = 1, s["base_price"]
            code = None
            if status == "confirmed":
                while True:
                    code = "EVT-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
                    if code not in used_codes:
                        used_codes.add(code)
                        break
            if status != "cancelled":
                busy.add((v["id"], ev["event_date"]))
            b = {"id": len(bookings) + 1, "event_id": ev["id"], "service_id": s["id"],
                 "vendor_id": v["id"], "quantity": qty, "agreed_price": round(total, 2),
                 "status": status, "confirmation_code": code}
            bookings.append(b)
            return b
        return None

    for i in range(N_EVENTS):
        client = clients[i % len(clients)]
        etype = random.choices(EVENT_TYPES, EVENT_WEIGHTS)[0]
        completed = i < N_COMPLETED
        if completed:
            d = random_weekend(date(2026, 5, 1), date(2026, 10, 9))
            status = "completed"
        else:
            d = random_weekend(date(2026, 10, 23), date(2027, 9, 30))
            status = "booked" if random.random() < 0.6 else "planning"
        city = random.choice(CITIES)
        lo, hi = GUESTS[etype]
        ev = {"id": i + 1, "client_id": client["id"],
              "name": f"{client['last_name']} {etype.title()}",
              "event_type": etype, "event_date": d, "city": city, "county": COUNTY[city],
              "guest_count": random.randrange(lo, hi + 1, 5), "status": status,
              "notes": None}
        events.append(ev)

        if etype == "wedding":
            cats = ["Venue", "Photographer", "DJ", "Caterer"] + random.sample(
                ["Florist", "Photo Booth", "Videographer"], random.randint(1, 2))
        elif etype == "corporate":
            cats = ["Venue", "Caterer", "DJ"] + (["Photographer"] if random.random() < 0.5 else [])
        elif etype == "birthday":
            cats = ["DJ", "Photo Booth"] + random.sample(["Caterer", "Venue"], 1)
        else:
            cats = random.sample(CATEGORIES, random.randint(2, 3))

        if status == "completed":
            for c in cats:
                try_book(ev, c, "confirmed")
        elif status == "booked":
            for c in cats:
                try_book(ev, c, "confirmed" if random.random() < 0.8 else "pending")
        else:  # planning: a couple of tentative picks
            for c in random.sample(cats, random.randint(0, 2)):
                try_book(ev, c, "pending")

    # A couple of cancelled bookings so the budget view has something to ignore
    booked_events = [e for e in events if e["status"] == "booked"]
    for ev in random.sample(booked_events, min(2, len(booked_events))):
        used = {next(s["vendor_id"] for s in services if s["id"] == b["service_id"])
                for b in bookings if b["event_id"] == ev["id"]}
        try_book(ev, random.choice(["Photo Booth", "Videographer", "Florist"]), "cancelled")

    # Budgets: some events end up under budget, some over
    for ev in events:
        total = sum(b["agreed_price"] for b in bookings
                    if b["event_id"] == ev["id"] and b["status"] != "cancelled")
        if random.random() < 0.1:
            ev["budget"] = None
        elif total > 0:
            ev["budget"] = max(500, round(total * random.uniform(0.85, 1.35), -2))
        else:
            per = random.choice([60, 80, 100, 125]) if ev["event_type"] == "wedding" else random.choice([30, 45, 60])
            ev["budget"] = round(ev["guest_count"] * per, -2)

    # Availability: Fri/Sat/Sun rows for every vendor
    avail = {}
    d = TODAY
    while d <= date(2027, 10, 31):
        if d.weekday() in (4, 5, 6):
            for v in vendors:
                avail[(v["id"], d)] = random.random() < 0.2
        d += timedelta(days=1)
    for b in bookings:
        if b["status"] != "cancelled":
            ev = events[b["event_id"] - 1]
            avail[(b["vendor_id"], ev["event_date"])] = True

    # Reviews: real ones from completed events, plus some older general reviews
    reviews = []
    for b in bookings:
        ev = events[b["event_id"] - 1]
        if ev["status"] == "completed" and b["status"] == "confirmed" and random.random() < 0.85:
            r = random.choices([5, 4, 3, 2], [55, 30, 10, 5])[0]
            reviews.append({"id": len(reviews) + 1, "client_id": ev["client_id"],
                            "vendor_id": b["vendor_id"], "booking_id": b["id"],
                            "rating": r, "comment": random.choice(COMMENTS[r])})
    for _ in range(30):
        r = random.choices([5, 4, 3, 2], [55, 30, 10, 5])[0]
        reviews.append({"id": len(reviews) + 1, "client_id": random.choice(clients)["id"],
                        "vendor_id": random.choice(vendors)["id"], "booking_id": None,
                        "rating": r, "comment": random.choice(COMMENTS[r])})

    return categories, vendors, services, avail, clients, events, bookings, reviews


def main():
    url = os.getenv("DATABASE_URL_ADMIN")
    if not url:
        print("Missing DATABASE_URL_ADMIN in .env")
        return
    if input("This DELETES all existing rows in the 8 tables and reseeds. Type 'yes' to continue: ") != "yes":
        print("Cancelled.")
        return

    categories, vendors, services, avail, clients, events, bookings, reviews = build_data()

    with psycopg.connect(url) as conn:
        cur = conn.cursor()
        cur.execute("TRUNCATE reviews, bookings, events, clients, availability, services, "
                    "vendors, categories RESTART IDENTITY CASCADE")

        cur.executemany("INSERT INTO categories (id, name) VALUES (%s, %s)",
                        [(c["id"], c["name"]) for c in categories])
        cur.executemany(
            "INSERT INTO vendors (id, name, category_id, description, city, county, email, phone) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            [(v["id"], v["name"], v["category_id"], v["description"], v["city"], v["county"],
              v["email"], v["phone"]) for v in vendors])
        cur.executemany(
            "INSERT INTO services (id, vendor_id, name, description, base_price, price_unit, min_guests, max_guests) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            [(s["id"], s["vendor_id"], s["name"], s["description"], s["base_price"], s["price_unit"],
              s["min_guests"], s["max_guests"]) for s in services])
        cur.executemany(
            "INSERT INTO availability (vendor_id, date, is_booked) VALUES (%s, %s, %s)",
            [(vid, d, booked) for (vid, d), booked in avail.items()])
        cur.executemany(
            "INSERT INTO clients (id, first_name, last_name, email, phone) VALUES (%s, %s, %s, %s, %s)",
            [(c["id"], c["first_name"], c["last_name"], c["email"], c["phone"]) for c in clients])
        cur.executemany(
            "INSERT INTO events (id, client_id, name, event_type, event_date, city, county, guest_count, budget, status, notes) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            [(e["id"], e["client_id"], e["name"], e["event_type"], e["event_date"], e["city"], e["county"],
              e["guest_count"], e["budget"], e["status"], e["notes"]) for e in events])
        cur.executemany(
            "INSERT INTO bookings (id, event_id, service_id, quantity, agreed_price, status, confirmation_code) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            [(b["id"], b["event_id"], b["service_id"], b["quantity"], b["agreed_price"], b["status"],
              b["confirmation_code"]) for b in bookings])
        cur.executemany(
            "INSERT INTO reviews (id, client_id, vendor_id, booking_id, rating, comment) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            [(r["id"], r["client_id"], r["vendor_id"], r["booking_id"], r["rating"], r["comment"])
             for r in reviews])

        # Explicit ids were used, so move each id counter past the highest one
        for t in ["categories", "vendors", "services", "availability", "clients",
                  "events", "bookings", "reviews"]:
            cur.execute(f"SELECT setval(pg_get_serial_sequence('public.{t}', 'id'), "
                        f"COALESCE((SELECT MAX(id) FROM public.{t}), 1))")
        conn.commit()

        print("Seeded:")
        for t in ["categories", "vendors", "services", "availability", "clients",
                  "events", "bookings", "reviews"]:
            n = cur.execute(f"SELECT count(*) FROM public.{t}").fetchone()[0]
            print(f"  {t:<13} {n}")
        over = cur.execute("SELECT count(*) FROM event_budget_summary WHERE within_budget = false").fetchone()[0]
        print(f"Events over budget: {over}")


if __name__ == "__main__":
    main()