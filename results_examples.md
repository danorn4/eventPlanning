# Results: same questions, different prompting strategies

Model: `gpt-6-luna`. 'Ran' means the SQL executed without error. It does NOT mean the answer is correct. Check the 'Correct?' lines by hand.

## Summary (did the SQL run?)

| Question | zero_shot (schema only) | single_domain (schema + examples) | cross_domain (schema + library examples) | zero_shot + notes |
|---|---|---|---|---|
| Which DJs are in Provo? | ran | ran | ran | ran |
| Which caterers charge the least per person? | ran | ran | ran | ran |
| Which venues can hold at least 200 guests? | ran | ran | ran | ran |
| Which clients have more than one event? | ran | ran | ran | ran |
| What is the total confirmed booking cost for each event in 2027? | ran | ran | ran | ran |
| Which vendors have an average rating of 4.5 or higher? | ran | ran | ran | ran |
| Which florists are free on 2027-06-12? | ran | ran | ran | ran |
| Which photo boths are in Orem? | ran | ran | ran | ran |
| What's the cheapest way to cover catering and a photo booth for 100 guests? | ran | ran | ran | ran |
| Find me something cozy and rustic | ran | ran | ran | ran |

## Details

### Which DJs are in Provo?

**zero_shot (schema only)** (811+171 tokens)

```sql
SELECT v.name
FROM vendors AS v
JOIN categories AS c ON c.id = v.category_id
WHERE v.city = 'Provo'
  AND LOWER(c.name) IN ('dj', 'djs')
```
Answer: Wasatch Beats DJ Co.

Correct? (fill in: yes / no / partly, and why)

**single_domain (schema + examples)** (1117+93 tokens)

```sql
SELECT v.name
FROM vendors v
JOIN categories c ON c.id = v.category_id
WHERE c.name = 'DJ' AND v.city = 'Provo'
```
Answer: Wasatch Beats DJ Co.

Correct? (fill in: yes / no / partly, and why)

**cross_domain (schema + library examples)** (989+79 tokens)

```sql
SELECT v.name
FROM vendors v
JOIN categories c ON c.id = v.category_id
WHERE c.name = 'DJ'
  AND v.city = 'Provo'
```
Answer: Wasatch Beats DJ Co.

Correct? (fill in: yes / no / partly, and why)

**zero_shot + notes** (1023+99 tokens)

```sql
SELECT v.name
FROM vendors AS v
JOIN categories AS c ON c.id = v.category_id
WHERE c.name = 'DJ'
  AND v.city = 'Provo'
```
Answer: Wasatch Beats DJ Co.

Correct? (fill in: yes / no / partly, and why)

### Which caterers charge the least per person?

**zero_shot (schema only)** (931+322 tokens)

```sql
SELECT v.name AS caterer, s.name AS service, s.base_price AS price_per_person
FROM vendors v
JOIN categories c ON c.id = v.category_id
JOIN services s ON s.vendor_id = v.id
WHERE c.name ILIKE '%cater%'
  AND s.price_unit = 'per_person'
  AND s.base_price = (
    SELECT MIN(s2.base_price)
    FROM vendors v2
    JOIN categories c2 ON c2.id = v2.category_id
    JOIN services s2 ON s2.vendor_id = v2.id
    WHERE c2.name ILIKE '%cater%'
      AND s2.price_unit = 'per_person'
  )
```
Answer: Desert Spoon Catering has the lowest per-person price: **$27 per person** for its Buffet dinner service.

Correct? (fill in: yes / no / partly, and why)

**single_domain (schema + examples)** (1360+200 tokens)

```sql
SELECT v.name, s.name AS service, s.base_price AS price_per_person
FROM vendors v
JOIN categories c ON c.id = v.category_id
JOIN services s ON s.vendor_id = v.id
WHERE c.name = 'Caterer'
  AND s.price_unit = 'per_person'
ORDER BY s.base_price ASC
```
Answer: Desert Spoon Catering charges the least: **$27 per person** for a buffet dinner.

Correct? (fill in: yes / no / partly, and why)

**cross_domain (schema + library examples)** (1078+344 tokens)

```sql
SELECT v.name, s.base_price AS price_per_person
FROM vendors v
JOIN categories c ON c.id = v.category_id
JOIN services s ON s.vendor_id = v.id
WHERE c.name = 'Catering'
  AND s.price_unit = 'per_person'
  AND s.base_price = (
    SELECT MIN(s2.base_price)
    FROM vendors v2
    JOIN categories c2 ON c2.id = v2.category_id
    JOIN services s2 ON s2.vendor_id = v2.id
    WHERE c2.name = 'Catering'
      AND s2.price_unit = 'per_person'
  )
```
Answer: Nothing matched.

Correct? (fill in: yes / no / partly, and why)

**zero_shot + notes** (1155+279 tokens)

```sql
SELECT v.name AS caterer, s.name AS service, s.base_price AS price_per_person
FROM vendors AS v
JOIN categories AS c ON c.id = v.category_id
JOIN services AS s ON s.vendor_id = v.id
WHERE c.name = 'Caterer'
  AND s.price_unit = 'per_person'
  AND s.base_price = (
    SELECT MIN(s2.base_price)
    FROM vendors AS v2
    JOIN categories AS c2 ON c2.id = v2.category_id
    JOIN services AS s2 ON s2.vendor_id = v2.id
    WHERE c2.name = 'Caterer'
      AND s2.price_unit = 'per_person'
  )
```
Answer: Desert Spoon Catering charges the least at $27 per person for its buffet dinner.

Correct? (fill in: yes / no / partly, and why)

### Which venues can hold at least 200 guests?

**zero_shot (schema only)** (942+280 tokens)

```sql
SELECT DISTINCT v.id, v.name, v.city, s.max_guests AS capacity
FROM vendors AS v
JOIN categories AS c ON c.id = v.category_id
JOIN services AS s ON s.vendor_id = v.id
WHERE c.name = 'Venue'
  AND s.max_guests >= 200
```
Answer: Venues that can hold at least 200 guests:

- Vineyard Hall at Lehi — Lehi — 200 guests
- Temple View Gardens — Provo — 300 guests
- Silver Lake Lodge — Park City — 250 guests
- The Brickyard Loft — Salt Lake City — 200 guests

Correct? (fill in: yes / no / partly, and why)

**single_domain (schema + examples)** (1358+246 tokens)

```sql
SELECT v.name, s.name AS service, s.max_guests
FROM vendors v
JOIN categories c ON c.id = v.category_id
JOIN services s ON s.vendor_id = v.id
WHERE c.name = 'Venue' AND s.max_guests >= 200
ORDER BY s.max_guests DESC
```
Answer: These venues can hold at least 200 guests:

- Temple View Gardens — 300 guests
- Silver Lake Lodge — 250 guests
- The Brickyard Loft — 200 guests
- Vineyard Hall at Lehi — 200 guests

Correct? (fill in: yes / no / partly, and why)

**cross_domain (schema + library examples)** (1036+183 tokens)

```sql
SELECT DISTINCT v.name
FROM vendors v
JOIN categories c ON c.id = v.category_id
JOIN services s ON s.vendor_id = v.id
WHERE c.name = 'Venue'
  AND s.max_guests >= 200
```
Answer: Venues that can hold at least 200 guests:

- Silver Lake Lodge
- Temple View Gardens
- The Brickyard Loft
- Vineyard Hall at Lehi

Correct? (fill in: yes / no / partly, and why)

**zero_shot + notes** (1219+343 tokens)

```sql
SELECT
  v.id,
  v.name,
  v.city,
  v.county,
  MAX(s.max_guests) AS capacity
FROM vendors AS v
JOIN categories AS c ON c.id = v.category_id
JOIN services AS s ON s.vendor_id = v.id
WHERE c.name = 'Venue'
  AND s.max_guests >= 200
GROUP BY v.id, v.name, v.city, v.county
ORDER BY v.name
```
Answer: Venues that can hold at least 200 guests:

- Silver Lake Lodge — Park City, Summit County — 250 guests
- Temple View Gardens — Provo, Utah County — 300 guests
- The Brickyard Loft — Salt Lake City, Salt Lake County — 200 guests
- Vineyard Hall at Lehi — Lehi, Utah County — 200 guests

Correct? (fill in: yes / no / partly, and why)

### Which clients have more than one event?

**zero_shot (schema only)** (1179+270 tokens)

```sql
SELECT c.id, c.first_name, c.last_name, c.email, c.phone
FROM clients AS c
JOIN events AS e ON e.client_id = c.id
GROUP BY c.id, c.first_name, c.last_name, c.email, c.phone
HAVING COUNT(e.id) > 1
```
Answer: Clients with more than one event:

- Ava Ellis
- Noah Dalton
- Ethan Fowler
- Liam Bennett
- Sophia Gardner
- Emma Anderson
- Mason Hansen
- Olivia Christensen

Correct? (fill in: yes / no / partly, and why)

**single_domain (schema + examples)** (1370+161 tokens)

```sql
SELECT c.id, c.first_name, c.last_name, COUNT(e.id) AS event_count
FROM clients c
JOIN events e ON e.client_id = c.id
GROUP BY c.id, c.first_name, c.last_name
HAVING COUNT(e.id) > 1
ORDER BY event_count DESC
```
Answer: The clients with more than one event are Ava Ellis, Noah Dalton, Ethan Fowler, Liam Bennett, Sophia Gardner, Emma Anderson, Mason Hansen, and Olivia Christensen. Each has 2 events.

Correct? (fill in: yes / no / partly, and why)

**cross_domain (schema + library examples)** (1172+136 tokens)

```sql
SELECT c.id, c.first_name, c.last_name
FROM clients c
JOIN events e ON e.client_id = c.id
GROUP BY c.id, c.first_name, c.last_name
HAVING COUNT(e.id) > 1
```
Answer: The clients with more than one event are Ava Ellis, Noah Dalton, Ethan Fowler, Liam Bennett, Sophia Gardner, Emma Anderson, Mason Hansen, and Olivia Christensen.

Correct? (fill in: yes / no / partly, and why)

**zero_shot + notes** (1285+187 tokens)

```sql
SELECT
  c.id AS client_id,
  c.first_name,
  c.last_name,
  COUNT(e.id) AS event_count
FROM clients AS c
JOIN events AS e ON e.client_id = c.id
GROUP BY c.id, c.first_name, c.last_name
HAVING COUNT(e.id) > 1
```
Answer: These clients each have 2 events:

- Ava Ellis
- Noah Dalton
- Ethan Fowler
- Liam Bennett
- Sophia Gardner
- Emma Anderson
- Mason Hansen
- Olivia Christensen

Correct? (fill in: yes / no / partly, and why)

### What is the total confirmed booking cost for each event in 2027?

**zero_shot (schema only)** (1160+316 tokens)

```sql
SELECT
  e.id AS event_id,
  e.name AS event_name,
  COALESCE(SUM(b.agreed_price), 0) AS total_confirmed_booking_cost
FROM events AS e
LEFT JOIN bookings AS b
  ON b.event_id = e.id
  AND b.status = 'confirmed'
WHERE e.event_date >= DATE '2027-01-01'
  AND e.event_date < DATE '2028-01-01'
GROUP BY e.id, e.name
```
Answer: Confirmed booking costs for each 2027 event:

| Event | Total confirmed booking cost |
|---|---:|
| Ingram Wedding | $14,729.00 |
| Mitchell Birthday | $1,010.00 |
| Nelson Graduation | $2,460.00 |
| Olsen Birthday | $2,915.00 |
| Peterson Wedding | $16,375.00 |
| Anderson Wedding | $14,425.00 |
| Christensen Wedding | $0 |
| Ellis Birthday | $1,725.00 |
| Gardner Wedding | $4,600.00 |
| Hansen Wedding | $0 |

Correct? (fill in: yes / no / partly, and why)

**single_domain (schema + examples)** (1515+359 tokens)

```sql
SELECT e.id AS event_id, e.name AS event_name, e.event_date, SUM(b.agreed_price) AS total_confirmed_booking_cost
FROM events e
JOIN bookings b ON b.event_id = e.id
WHERE e.event_date >= '2027-01-01'
  AND e.event_date < '2028-01-01'
  AND b.status = 'confirmed'
GROUP BY e.id, e.name, e.event_date
ORDER BY e.event_date
```
Answer: Confirmed booking costs for events in 2027:

| Event | Date | Total cost |
|---|---|---:|
| Gardner Wedding | Jan 1, 2027 | $4,600.00 |
| Peterson Wedding | Jan 15, 2027 | $16,375.00 |
| Ingram Wedding | Jan 29, 2027 | $14,729.00 |
| Olsen Birthday | Mar 26, 2027 | $2,915.00 |
| Mitchell Birthday | Apr 17, 2027 | $1,010.00 |
| Anderson Wedding | Jun 12, 2027 | $14,425.00 |
| Ellis Birthday | Aug 20, 2027 | $1,725.00 |
| Nelson Graduation | Sep 4, 2027 | $2,460.00 |

Correct? (fill in: yes / no / partly, and why)

**cross_domain (schema + library examples)** (1349+313 tokens)

```sql
SELECT
  e.id AS event_id,
  e.name AS event_name,
  COALESCE(SUM(b.agreed_price), 0) AS total_confirmed_booking_cost
FROM events e
LEFT JOIN bookings b
  ON b.event_id = e.id
  AND b.status = 'confirmed'
WHERE e.event_date >= DATE '2027-01-01'
  AND e.event_date < DATE '2028-01-01'
GROUP BY e.id, e.name
ORDER BY e.id
```
Answer: Confirmed booking costs for each 2027 event:

| Event | Total |
|---|---:|
| Ingram Wedding | $14,729.00 |
| Mitchell Birthday | $1,010.00 |
| Nelson Graduation | $2,460.00 |
| Olsen Birthday | $2,915.00 |
| Peterson Wedding | $16,375.00 |
| Anderson Wedding | $14,425.00 |
| Christensen Wedding | $0 |
| Ellis Birthday | $1,725.00 |
| Gardner Wedding | $4,600.00 |
| Hansen Wedding | $0 |

Correct? (fill in: yes / no / partly, and why)

**zero_shot + notes** (1507+425 tokens)

```sql
SELECT
  e.id AS event_id,
  e.name AS event_name,
  e.event_date,
  COALESCE(SUM(b.agreed_price), 0) AS total_confirmed_booking_cost
FROM events AS e
LEFT JOIN bookings AS b
  ON b.event_id = e.id
  AND b.status = 'confirmed'
WHERE e.event_date >= DATE '2027-01-01'
  AND e.event_date < DATE '2028-01-01'
GROUP BY e.id, e.name, e.event_date
```
Answer: | Event | Date | Confirmed booking cost |
|---|---|---:|
| Ingram Wedding | Jan 29, 2027 | $14,729.00 |
| Mitchell Birthday | Apr 17, 2027 | $1,010.00 |
| Nelson Graduation | Sep 4, 2027 | $2,460.00 |
| Olsen Birthday | Mar 26, 2027 | $2,915.00 |
| Peterson Wedding | Jan 15, 2027 | $16,375.00 |
| Anderson Wedding | Jun 12, 2027 | $14,425.00 |
| Christensen Wedding | Aug 6, 2027 | $0.00 |
| Ellis Birthday | Aug 20, 2027 | $1,725.00 |
| Gardner Wedding | Jan 1, 2027 | $4,600.00 |
| Hansen Wedding | Feb 13, 2027 | $0.00 |

Correct? (fill in: yes / no / partly, and why)

### Which vendors have an average rating of 4.5 or higher?

**zero_shot (schema only)** (1115+247 tokens)

```sql
SELECT v.id, v.name
FROM vendors AS v
JOIN vendor_ratings AS vr ON vr.vendor_id = v.id
WHERE vr.avg_rating >= 4.5
```
Answer: The vendors with an average rating of 4.5 or higher are:

- Silver Peak Sound
- Beehive Beats
- Golden Hour Studio
- Summit Light Photography
- Saltflat Portraits
- Peach Pit Catering
- Sego Lily Kitchen
- Desert Spoon Catering
- Vineyard Hall at Lehi
- Silver Lake Lodge
- Junction City Ballroom
- The Brickyard Loft
- Snap Happy Booths
- Click & Giggle Booths
- Red Rock Booth Co.
- Frame & Fun Booths
- Wildflower & Sage
- Petal Pushers of Park City
- Northstar Films
- Sunset Reel Co.

Correct? (fill in: yes / no / partly, and why)

**single_domain (schema + examples)** (1647+364 tokens)

```sql
SELECT v.name, v.city, r.avg_rating
FROM vendors v
JOIN vendor_ratings r ON r.vendor_id = v.id
WHERE r.avg_rating >= 4.5
ORDER BY r.avg_rating DESC
```
Answer: Vendors rated 4.5 or higher:

- Silver Peak Sound — Lehi (5.00)
- Beehive Beats — Salt Lake City (5.00)
- Golden Hour Studio — Provo (5.00)
- Summit Light Photography — Park City (5.00)
- Saltflat Portraits — Salt Lake City (5.00)
- Red Rock Booth Co. — St. George (5.00)
- Wildflower & Sage — Salt Lake City (5.00)
- Petal Pushers of Park City — Park City (5.00)
- Northstar Films — Salt Lake City (5.00)
- Desert Spoon Catering — St. George (5.00)
- Vineyard Hall at Lehi — Lehi (5.00)
- Silver Lake Lodge — Park City (5.00)
- Junction City Ballroom — Ogden (5.00)
- The Brickyard Loft — Salt Lake City (5.00)
- Snap Happy Booths — Orem (5.00)
- Click & Giggle Booths — Lehi (5.00)
- Frame & Fun Booths — Ogden (4.67)
- Peach Pit Catering — Springville (4.50)
- Sego Lily Kitchen — Salt Lake City (4.50)
- Sunset Reel Co. — St. George (4.50)

Correct? (fill in: yes / no / partly, and why)

**cross_domain (schema + library examples)** (1176+217 tokens)

```sql
SELECT v.name
FROM vendors v
JOIN vendor_ratings vr ON vr.vendor_id = v.id
WHERE vr.avg_rating >= 4.5
```
Answer: The vendors with an average rating of 4.5 or higher are:

- Silver Peak Sound
- Beehive Beats
- Golden Hour Studio
- Summit Light Photography
- Saltflat Portraits
- Peach Pit Catering
- Sego Lily Kitchen
- Desert Spoon Catering
- Vineyard Hall at Lehi
- Silver Lake Lodge
- Junction City Ballroom
- The Brickyard Loft
- Snap Happy Booths
- Click & Giggle Booths
- Red Rock Booth Co.
- Frame & Fun Booths
- Wildflower & Sage
- Petal Pushers of Park City
- Northstar Films
- Sunset Reel Co.

Correct? (fill in: yes / no / partly, and why)

**zero_shot + notes** (1393+341 tokens)

```sql
SELECT v.name, vr.avg_rating
FROM vendors AS v
JOIN vendor_ratings AS vr ON vr.vendor_id = v.id
WHERE vr.avg_rating >= 4.5
```
Answer: Vendors with an average rating of 4.5 or higher:

- Silver Peak Sound — 5.00
- Beehive Beats — 5.00
- Golden Hour Studio — 5.00
- Summit Light Photography — 5.00
- Saltflat Portraits — 5.00
- Peach Pit Catering — 4.50
- Sego Lily Kitchen — 4.50
- Desert Spoon Catering — 5.00
- Vineyard Hall at Lehi — 5.00
- Silver Lake Lodge — 5.00
- Junction City Ballroom — 5.00
- The Brickyard Loft — 5.00
- Snap Happy Booths — 5.00
- Click & Giggle Booths — 5.00
- Red Rock Booth Co. — 5.00
- Frame & Fun Booths — 4.67
- Wildflower & Sage — 5.00
- Petal Pushers of Park City — 5.00
- Northstar Films — 5.00
- Sunset Reel Co. — 4.50

Correct? (fill in: yes / no / partly, and why)

### Which florists are free on 2027-06-12?

**zero_shot (schema only)** (904+326 tokens)

```sql
SELECT v.id, v.name
FROM vendors AS v
JOIN categories AS c ON c.id = v.category_id
WHERE c.name ILIKE '%florist%'
  AND NOT EXISTS (
    SELECT 1
    FROM availability AS a
    WHERE a.vendor_id = v.id
      AND a.date = DATE '2027-06-12'
      AND a.is_booked = TRUE
  )
```
Answer: The florists listed as free on June 12, 2027, are Wildflower & Sage, Petal Pushers of Park City, and Rosewood Floral Studio.

Correct? (fill in: yes / no / partly, and why)

**single_domain (schema + examples)** (1202+160 tokens)

```sql
SELECT v.name, v.city
FROM vendors v
JOIN categories c ON c.id = v.category_id
JOIN availability a ON a.vendor_id = v.id
WHERE c.name = 'Florist'
  AND a.date = '2027-06-12'
  AND a.is_booked = false
```
Answer: These florists are free on June 12, 2027:

- Wildflower & Sage — Salt Lake City
- Petal Pushers of Park City — Park City
- Rosewood Floral Studio — Logan

Correct? (fill in: yes / no / partly, and why)

**cross_domain (schema + library examples)** (1050+173 tokens)

```sql
SELECT DISTINCT v.name
FROM vendors v
JOIN categories c ON c.id = v.category_id
JOIN availability a ON a.vendor_id = v.id
WHERE c.name = 'Florist'
  AND a.date = DATE '2027-06-12'
  AND a.is_booked = FALSE
```
Answer: Petal Pushers of Park City, Rosewood Floral Studio, and Wildflower & Sage are free on 2027-06-12.

Correct? (fill in: yes / no / partly, and why)

**zero_shot + notes** (1119+257 tokens)

```sql
SELECT v.id, v.name
FROM vendors AS v
JOIN categories AS c ON c.id = v.category_id
WHERE c.name = 'Florist'
  AND EXISTS (
    SELECT 1
    FROM availability AS a
    WHERE a.vendor_id = v.id
      AND a.date = DATE '2027-06-12'
      AND a.is_booked = FALSE
  )
```
Answer: The florists available on June 12, 2027, are Wildflower & Sage, Petal Pushers of Park City, and Rosewood Floral Studio.

Correct? (fill in: yes / no / partly, and why)

### Which photo boths are in Orem?

**zero_shot (schema only)** (810+170 tokens)

```sql
SELECT v.name
FROM vendors AS v
JOIN categories AS c ON c.id = v.category_id
WHERE c.name ILIKE '%photo booth%'
  AND v.city = 'Orem'
```
Answer: Snap Happy Booths

Correct? (fill in: yes / no / partly, and why)

**single_domain (schema + examples)** (1121+141 tokens)

```sql
SELECT v.name
FROM vendors v
JOIN categories c ON c.id = v.category_id
WHERE c.name = 'Photo Booth' AND v.city = 'Orem'
```
Answer: Snap Happy Booths is the photo booth vendor in Orem.

Correct? (fill in: yes / no / partly, and why)

**cross_domain (schema + library examples)** (996+230 tokens)

```sql
SELECT v.name
FROM vendors v
JOIN categories c ON c.id = v.category_id
WHERE LOWER(c.name) LIKE '%photo booth%'
  AND LOWER(v.city) = 'orem'
```
Answer: Snap Happy Booths is in Orem.

Correct? (fill in: yes / no / partly, and why)

**zero_shot + notes** (1027+126 tokens)

```sql
SELECT v.name
FROM vendors AS v
JOIN categories AS c ON c.id = v.category_id
WHERE c.name = 'Photo Booth'
  AND v.city = 'Orem'
```
Answer: Snap Happy Booths is in Orem.

Correct? (fill in: yes / no / partly, and why)

### What's the cheapest way to cover catering and a photo booth for 100 guests?

**zero_shot (schema only)** (1270+1570 tokens)

```sql
WITH eligible_services AS (
  SELECT
    CASE
      WHEN c.name ILIKE '%cater%' THEN 'catering'
      WHEN c.name ILIKE '%photo%booth%' OR s.name ILIKE '%photo%booth%' THEN 'photo_booth'
    END AS service_type,
    v.name AS vendor_name,
    s.name AS service_name,
    s.price_unit,
    s.base_price,
    s.base_price * CASE
      WHEN s.price_unit IN ('per_person', 'per_item') THEN 100
      ELSE 1
    END AS estimated_cost
  FROM services s
  JOIN vendors v ON v.id = s.vendor_id
  JOIN categories c ON c.id = v.category_id
  WHERE (
      c.name ILIKE '%cater%'
      OR c.name ILIKE '%photo%booth%'
      OR s.name ILIKE '%photo%booth%'
    )
    AND (s.min_guests IS NULL OR s.min_guests <= 100)
    AND (s.max_guests IS NULL OR s.max_guests >= 100)
),
catering AS (
  SELECT * FROM eligible_services WHERE service_type = 'catering'
),
photo_booths AS (
  SELECT * FROM eligible_services WHERE service_type = 'photo_booth'
)
SELECT
  catering.vendor_name AS catering_vendor,
  catering.service_name AS catering_service,
  catering.price_unit AS catering_price_unit,
  catering.estimated_cost AS catering_estimated_cost,
  photo_booths.vendor_name AS photo_booth_vendor,
  photo_booths.service_name AS photo_booth_service,
  photo_booths.price_unit AS photo_booth_price_unit,
  photo_booths.estimated_cost AS photo_booth_estimated_cost,
  catering.estimated_cost + photo_booths.estimated_cost AS total_estimated_cost
FROM catering
CROSS JOIN photo_booths
ORDER BY total_estimated_cost
LIMIT 1
```
Answer: The cheapest matching combination is **Mountain Table Catering’s Dessert Table** for **$700** plus **Frame & Fun Booths’ Additional Booth Hour** for **$105**, totaling **$805**.

Note: the listed services are a dessert table and an additional booth hour, so they may not provide full catering or a complete photo-booth package.

Correct? (fill in: yes / no / partly, and why)

**single_domain (schema + examples)** (1373+896 tokens)

```sql
WITH service_options AS (
  SELECT
    c.name AS category,
    v.name AS vendor,
    s.name AS service,
    s.base_price,
    s.price_unit,
    CASE
      WHEN s.price_unit = 'per_person' THEN s.base_price * 100
      ELSE s.base_price
    END AS estimated_cost
  FROM services s
  JOIN vendors v ON v.id = s.vendor_id
  JOIN categories c ON c.id = v.category_id
  WHERE c.name IN ('Catering', 'Photo Booth')
    AND (s.min_guests IS NULL OR s.min_guests <= 100)
    AND (s.max_guests IS NULL OR s.max_guests >= 100)
),
catering_options AS (
  SELECT * FROM service_options WHERE category = 'Catering'
),
photo_booth_options AS (
  SELECT * FROM service_options WHERE category = 'Photo Booth'
)
SELECT
  c.vendor AS catering_vendor,
  c.service AS catering_service,
  c.estimated_cost AS catering_cost,
  p.vendor AS photo_booth_vendor,
  p.service AS photo_booth_service,
  p.estimated_cost AS photo_booth_cost,
  c.estimated_cost + p.estimated_cost AS total_estimated_cost
FROM catering_options c
CROSS JOIN photo_booth_options p
ORDER BY total_estimated_cost
LIMIT 1
```
Answer: Nothing matched—no catering and photo booth combination was returned for 100 guests.

Correct? (fill in: yes / no / partly, and why)

**cross_domain (schema + library examples)** (1337+805 tokens)

```sql
WITH priced_services AS (
  SELECT
    s.id AS service_id,
    s.name AS service_name,
    v.name AS vendor_name,
    c.name AS category_name,
    s.price_unit,
    s.base_price,
    CASE
      WHEN s.price_unit = 'per_person' THEN s.base_price * 100
      ELSE s.base_price
    END AS estimated_price
  FROM services s
  JOIN vendors v ON v.id = s.vendor_id
  JOIN categories c ON c.id = v.category_id
  WHERE (s.min_guests IS NULL OR s.min_guests <= 100)
    AND (s.max_guests IS NULL OR s.max_guests >= 100)
),
catering AS (
  SELECT *
  FROM priced_services
  WHERE category_name ILIKE '%cater%'
),
photo_booths AS (
  SELECT *
  FROM priced_services
  WHERE category_name ILIKE '%photo%booth%'
)
SELECT
  ca.vendor_name AS catering_vendor,
  ca.service_name AS catering_service,
  ca.estimated_price AS catering_estimated_price,
  pb.vendor_name AS photo_booth_vendor,
  pb.service_name AS photo_booth_service,
  pb.estimated_price AS photo_booth_estimated_price,
  ca.estimated_price + pb.estimated_price AS total_estimated_price
FROM catering ca
CROSS JOIN photo_booths pb
ORDER BY total_estimated_price
LIMIT 1
```
Answer: The cheapest combination is Mountain Table Catering’s dessert table ($700) and Frame & Fun Booths’ additional booth hour ($105), for an estimated total of **$805**.

Correct? (fill in: yes / no / partly, and why)

**zero_shot + notes** (1456+1614 tokens)

```sql
WITH eligible_services AS (
    SELECT
        c.name AS category_name,
        v.name AS vendor_name,
        s.name AS service_name,
        s.price_unit,
        s.base_price,
        CASE
            WHEN s.price_unit = 'per_person' THEN s.base_price * 100
            ELSE s.base_price
        END AS estimated_cost
    FROM services s
    JOIN vendors v ON v.id = s.vendor_id
    JOIN categories c ON c.id = v.category_id
    WHERE lower(c.name) IN ('caterer', 'photo booth')
      AND (s.min_guests IS NULL OR s.min_guests <= 100)
      AND (s.max_guests IS NULL OR s.max_guests >= 100)
      AND s.price_unit IN ('flat', 'per_person')
),
catering AS (
    SELECT *
    FROM eligible_services
    WHERE lower(category_name) = 'caterer'
),
photo_booths AS (
    SELECT *
    FROM eligible_services
    WHERE lower(category_name) = 'photo booth'
)
SELECT
    catering.vendor_name AS caterer_vendor,
    catering.service_name AS catering_service,
    catering.price_unit AS catering_price_unit,
    catering.estimated_cost AS catering_cost,
    photo_booths.vendor_name AS photo_booth_vendor,
    photo_booths.service_name AS photo_booth_service,
    photo_booths.price_unit AS photo_booth_price_unit,
    photo_booths.estimated_cost AS photo_booth_cost,
    catering.estimated_cost + photo_booths.estimated_cost AS total_estimated_cost
FROM catering
CROSS JOIN photo_booths
ORDER BY total_estimated_cost, catering.vendor_name, catering.service_name,
         photo_booths.vendor_name, photo_booths.service_name
LIMIT 1
```
Answer: The cheapest option is Mountain Table Catering’s dessert table for $700, plus Frame & Fun Booths’ custom backdrop & props upgrade for $150. Total estimated cost: **$850** for 100 guests.

Correct? (fill in: yes / no / partly, and why)

### Find me something cozy and rustic

**zero_shot (schema only)** (941+399 tokens)

```sql
SELECT
  v.id AS vendor_id,
  v.name AS vendor_name,
  c.name AS category,
  v.city,
  s.id AS service_id,
  s.name AS service_name,
  s.description AS service_description,
  s.base_price,
  s.price_unit,
  vr.avg_rating,
  vr.review_count
FROM vendors AS v
JOIN services AS s ON s.vendor_id = v.id
LEFT JOIN categories AS c ON c.id = v.category_id
LEFT JOIN vendor_ratings AS vr ON vr.vendor_id = v.id
WHERE concat_ws(' ', v.name, v.description, c.name, s.name, s.description) ILIKE '%cozy%'
  AND concat_ws(' ', v.name, v.description, c.name, s.name, s.description) ILIKE '%rustic%'
ORDER BY vr.avg_rating DESC NULLS LAST, vr.review_count DESC NULLS LAST
```
Answer: Nothing matched “cozy” and “rustic.”

Correct? (fill in: yes / no / partly, and why)

**single_domain (schema + examples)** (1196+275 tokens)

```sql
SELECT DISTINCT
  v.name AS vendor,
  c.name AS category,
  v.city,
  s.name AS service,
  s.base_price,
  s.price_unit
FROM vendors v
JOIN categories c ON c.id = v.category_id
LEFT JOIN services s ON s.vendor_id = v.id
WHERE CONCAT_WS(' ', v.name, v.description, c.name, s.name, s.description) ILIKE '%cozy%'
  AND CONCAT_WS(' ', v.name, v.description, c.name, s.name, s.description) ILIKE '%rustic%'
ORDER BY v.name, s.name
```
Answer: Nothing matched “cozy” and “rustic.”

Correct? (fill in: yes / no / partly, and why)

**cross_domain (schema + library examples)** (1063+373 tokens)

```sql
SELECT
  v.name AS vendor_name,
  c.name AS category,
  s.name AS service_name,
  s.description AS service_description,
  s.base_price,
  s.price_unit
FROM vendors v
JOIN services s ON s.vendor_id = v.id
LEFT JOIN categories c ON c.id = v.category_id
WHERE CONCAT_WS(' ', v.name, v.description, s.name, s.description, c.name) ILIKE '%cozy%'
  AND CONCAT_WS(' ', v.name, v.description, s.name, s.description, c.name) ILIKE '%rustic%'
```
Answer: Nothing matched “cozy” and “rustic.”

Correct? (fill in: yes / no / partly, and why)

**zero_shot + notes** (1468+1078 tokens)

```sql
SELECT
  v.id AS vendor_id,
  v.name AS vendor_name,
  c.name AS category,
  v.city,
  v.county,
  v.description,
  vr.avg_rating,
  vr.review_count,
  array_agg(DISTINCT s.name) FILTER (WHERE s.id IS NOT NULL) AS services
FROM vendors AS v
JOIN categories AS c ON c.id = v.category_id
LEFT JOIN vendor_ratings AS vr ON vr.vendor_id = v.id
LEFT JOIN services AS s ON s.vendor_id = v.id
WHERE concat_ws(' ', v.name, v.description, s.name, s.description) ILIKE ANY (
  ARRAY[
    '%cozy%',
    '%rustic%',
    '%barn%',
    '%farmhouse%',
    '%cabin%',
    '%woodland%',
    '%intimate%'
  ]
)
GROUP BY v.id, v.name, c.name, v.city, v.county, v.description, vr.avg_rating, vr.review_count
ORDER BY vr.avg_rating DESC NULLS LAST, v.name
```
Answer: Here are some rustic venue options:

- **Junction City Ballroom** — Ogden, Weber County. Rustic charm with modern amenities; rated **5.0** (1 review). Offers full-day venue rental and a ceremony space add-on.
- **Vineyard Hall at Lehi** — Lehi, Utah County. Rustic charm with modern amenities; rated **5.0** (2 reviews). Offers full-day venue rental and a tables-and-chairs package.
- **The Aspen Barn** — Heber City, Wasatch County. A setting for ceremonies and receptions; rated **4.0** (3 reviews). Offers full-day venue rental and a ceremony space add-on.

Correct? (fill in: yes / no / partly, and why)
