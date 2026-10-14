# Event Services Marketplace: Natural Language Interface

A database for an event-services marketplace (think "hotels.com for weddings and parties"), plus an AI interface that lets you ask questions about it in plain English.

Vendors such as DJs, photographers, caterers, venues, photo booths, florists, and videographers list their services. Clients plan events (weddings, birthdays, corporate parties) and book services for them. You can ask things like *"Which photographers in Provo cost under $2,000?"* or *"Which events are over budget?"* and get a plain-English answer.

## How it works

```
question -> LLM writes SQL -> checked, then run as a READ-ONLY database user -> rows -> LLM writes a plain-English answer
```
1. The schema (tables, columns, comments, foreign keys) is read live from Postgres and put into the prompt.
2. The LLM returns a SQL query.
3. The query is checked (single `SELECT` only) and run with a login that **cannot write**.
4. The rows go back to the LLM, which writes a short friendly answer using only that data.

Prompting strategies from the paper ["Evaluating the Text-to-SQL Capabilities of Large Language Models"](https://arxiv.org/abs/2305.11853) are supported:

| Strategy | What the prompt contains |
|---|---|
| `zero_shot` | Schema only |
| `single_domain` | Schema + example question/SQL pairs from this database |
| `cross_domain` | Schema + examples from a different database (a library) |

A `NOTES` block (allowed values, hints about the views) can be switched on or off, so you can measure how much it helps.

## Database

PostgreSQL hosted on Supabase, 8 tables and 2 views:

- `categories`, `vendors`, `services`, `availability`: what vendors offer and when they are free
- `clients`, `events`, `bookings`, `reviews`: who is planning what, what they booked, and how it went
- `vendor_ratings` (view): average rating per vendor
- `event_budget_summary` (view): total cost, budget remaining, and whether each event is within budget

The full definition is in [`schema.sql`](schema.sql). All seeded data is fake.

## Safety design

The model writes SQL, so the database is locked down instead of trusting the model:

- AI-generated queries run as `ai_readonly`, a login with `SELECT` only, read-only transactions, and a 5-second statement timeout ([`setup_readonly_role.sql`](setup_readonly_role.sql)).
- Row-level security is on for every table.
- The Supabase Data API is turned off, so the database is only reachable through the connection strings.
- The script also rejects anything that is not a single `SELECT` or `WITH` query, and caps results at 50 rows.
- Secrets live in `.env`, which is never committed.

## Setup

You need Python 3.10+, a free [Supabase](https://supabase.com) project, and an [OpenAI](https://platform.openai.com) API key.

1. **Install dependencies**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   pip install openai "psycopg[binary]" python-dotenv
   ```
2. **Create the database.** In the Supabase SQL Editor, run `schema.sql`, then `setup_readonly_role.sql` (change its password first).
3. **Configure secrets.** Copy `.env.example` to `.env` and fill in your two Supabase connection strings (session pooler), your OpenAI key, and a model name. Use the pooler username format `postgres.<project-ref>` and `ai_readonly.<project-ref>`.
4. **Check the connections**
   ```bash
   python test_connection.py
   ```
   All six checks should pass.
5. **Load the fake data** (this wipes the tables first)
   ```bash
   python seed.py
   ```

## Usage

```bash
python nl_query.py                                   # interactive, single_domain strategy
python nl_query.py -q "Which DJs are in Provo?"      # one question
python nl_query.py --strategy zero_shot --no-notes   # schema only, like the paper's zero-shot
python run_examples.py                               # run the test questions under every strategy
```

Every question is appended to `query_log.jsonl` (question, strategy, SQL, success, token counts). `run_examples.py` writes `results_examples.md` and `results_examples.json`.

## Files

| File | Purpose |
|---|---|
| `nl_query.py` | The main app: schema reading, prompting, safety checks, running SQL, logging |
| `run_examples.py` | Runs the same questions under several strategies and writes a results report |
| `schema.sql` | Tables, constraints, views, and column comments |
| `setup_readonly_role.sql` | Read-only login and row-level security |
| `seed.py` | Fills the database with fake Utah vendors, events, bookings, and reviews |
| `test_connection.py` | Confirms both logins work and that the read-only login cannot write |

## Cost

Each question sends roughly 1,500 to 3,000 tokens and gets back a few hundred, across two model calls, so it costs a fraction of a cent on a small model. Token counts are printed after every question, and cost estimates appear if you set `PRICE_IN_PER_M` and `PRICE_OUT_PER_M` in `.env`.

## Known limitations

- **Valid SQL is not always the right SQL.** The model can run a query that answers a slightly different question, and the friendly answer then sounds confident. Verify important answers.
- **No memory.** Each question stands alone, so follow-ups like "which of those are cheaper?" do not work.
- **Misspellings** are only corrected when the right value appears in the prompt (for example, category names). A misspelled city or vendor name will match nothing.
- **Vague requests** like "something cozy and rustic" have nothing in the schema to match.
- **Read-only.** It cannot create events or bookings.

## Ideas for going further

- Load distinct categories, cities, and counties into the prompt, or use fuzzy matching (`pg_trgm`) to fix typos.
- Add conversation memory so follow-up questions work.
- Use embeddings (`pgvector`) for style-based search, like "cozy and rustic".
- Add a wishlist/board feature and a web frontend.
- Let users create bookings through separate, tightly controlled code with its own write permissions.

## Security notes

Never commit `.env`. If a key or password is ever exposed, rotate it immediately (OpenAI dashboard for keys, Supabase Project Settings, then Database, for the database password).