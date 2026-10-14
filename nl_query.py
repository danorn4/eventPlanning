"""Ask questions about the event marketplace database in plain English.

Flow: question -> LLM writes SQL -> run it as the read-only role -> LLM turns the rows into an answer.

Usage:
    python nl_query.py                                  # interactive, single_domain strategy
    python nl_query.py --strategy zero_shot             # zero_shot | single_domain | cross_domain
    python nl_query.py --strategy zero_shot --no-notes  # schema only, like the paper's zero-shot
    python nl_query.py -q "Which DJs are in Provo?"     # one question, then exit

Needs in .env: DATABASE_URL_READONLY, OPENAI_API_KEY, OPENAI_MODEL
Optional in .env: OPENAI_ANSWER_MODEL (defaults to OPENAI_MODEL),
                  PRICE_IN_PER_M and PRICE_OUT_PER_M (USD per 1M tokens, for cost estimates)
"""
import argparse
import json
import os
import re
from datetime import date, datetime

import psycopg
from dotenv import load_dotenv
from openai import OpenAI
from psycopg.rows import dict_row

load_dotenv()

DB_URL = os.getenv("DATABASE_URL_READONLY")
SQL_MODEL = os.getenv("OPENAI_MODEL")
ANSWER_MODEL = os.getenv("OPENAI_ANSWER_MODEL") or SQL_MODEL
PRICE_IN = float(os.getenv("PRICE_IN_PER_M", 0) or 0)
PRICE_OUT = float(os.getenv("PRICE_OUT_PER_M", 0) or 0)
MAX_ROWS = 50
LOG_FILE = "query_log.jsonl"

NOTES = f"""Notes about this database:
- Today's date is {date.today().isoformat()}. Dates in the database are real calendar dates.
- bookings.status is one of: pending, confirmed, cancelled.
- events.status is one of: planning, booked, completed, cancelled.
- events.event_type is one of: wedding, birthday, corporate, anniversary, graduation, other.
- services.price_unit is one of: flat, per_hour, per_person, per_item.
- A vendor's category name is in categories.name (DJ, Photographer, Caterer, Venue, Photo Booth, Florist, Videographer).
- Vendor location is vendors.city and vendors.county (county values look like 'Utah', 'Salt Lake', 'Summit').
- Use the vendor_ratings view for average ratings and the event_budget_summary view for budget questions.
- A vendor is free on a date if an availability row exists for that date with is_booked = false.
  Availability rows exist only for Fridays, Saturdays, and Sundays.
- Write PostgreSQL. Return exactly one read-only SELECT statement."""

SINGLE_DOMAIN_EXAMPLES = """Examples (same database):

Question: Which photographers in Provo cost less than $2,000?
SQL:
SELECT v.name, s.name AS service, s.base_price, s.price_unit
FROM vendors v
JOIN categories c ON c.id = v.category_id
JOIN services s ON s.vendor_id = v.id
WHERE c.name = 'Photographer' AND v.city = 'Provo' AND s.base_price < 2000
ORDER BY s.base_price;

Question: Which DJs are free on 2026-11-14 and rated above 4.5?
SQL:
SELECT v.name, v.city, r.avg_rating
FROM vendors v
JOIN categories c ON c.id = v.category_id
JOIN availability a ON a.vendor_id = v.id AND a.date = '2026-11-14' AND a.is_booked = false
JOIN vendor_ratings r ON r.vendor_id = v.id
WHERE c.name = 'DJ' AND r.avg_rating > 4.5;

Question: Which events are over budget?
SQL:
SELECT event_name, event_date, budget, total_cost, budget_remaining
FROM event_budget_summary
WHERE within_budget = false;

Question: What is the average vendor rating for each category?
SQL:
SELECT c.name AS category, ROUND(AVG(r.avg_rating), 2) AS avg_rating
FROM categories c
JOIN vendors v ON v.category_id = c.id
JOIN vendor_ratings r ON r.vendor_id = v.id
GROUP BY c.name
ORDER BY avg_rating DESC;"""

# Examples from a DIFFERENT database (a library), to test the cross-domain strategy
CROSS_DOMAIN_EXAMPLES = """Examples (from a different database, a library):

Schema:
authors(id, name)
books(id, title, author_id -> authors.id, published_year)
loans(id, book_id -> books.id, member_id, loaned_on, returned_on)

Question: Which books by Jane Austen are currently checked out?
SQL:
SELECT b.title
FROM books b
JOIN authors a ON a.id = b.author_id
JOIN loans l ON l.book_id = b.id
WHERE a.name = 'Jane Austen' AND l.returned_on IS NULL;

Question: How many books were loaned out in each month of 2024?
SQL:
SELECT DATE_TRUNC('month', loaned_on) AS month, COUNT(*) AS loans
FROM loans
WHERE loaned_on >= '2024-01-01' AND loaned_on < '2025-01-01'
GROUP BY month
ORDER BY month;"""

BAD_WORDS = re.compile(
    r"\b(insert|update|delete|drop|alter|create|grant|revoke|truncate|copy|call|do|execute)\b", re.I)


def get_schema_text(conn):
    """Describe tables, columns, comments, and foreign keys by reading the live database."""
    cols = conn.execute("""
        SELECT c.table_name, c.column_name, c.data_type, c.is_nullable,
               col_description(cl.oid, c.ordinal_position::int) AS comment
        FROM information_schema.columns c
        JOIN pg_class cl ON cl.relname = c.table_name AND cl.relnamespace = 'public'::regnamespace
        WHERE c.table_schema = 'public'
        ORDER BY c.table_name, c.ordinal_position
    """).fetchall()
    fks = conn.execute("""
        SELECT conrelid::regclass::text AS tbl, pg_get_constraintdef(oid) AS def
        FROM pg_constraint WHERE contype = 'f' AND connamespace = 'public'::regnamespace
    """).fetchall()

    tables = {}
    for r in cols:
        line = f"  {r['column_name']} {r['data_type']}"
        if r["is_nullable"] == "YES":
            line += " NULL"
        if r["comment"]:
            line += f"  -- {r['comment']}"
        tables.setdefault(r["table_name"], []).append(line)

    out = ["Database schema (PostgreSQL):"]
    for t, lines in tables.items():
        out.append(f"\nTABLE {t} (")
        out.extend(lines)
        out.append(")")
    out.append("\nForeign keys:")
    for r in fks:
        out.append(f"  {r['tbl']}: {r['def']}")
    return "\n".join(out)


def build_prompt(schema, question, strategy, use_notes=True):
    parts = [schema] + ([NOTES] if use_notes else [])
    if strategy == "single_domain":
        parts.append(SINGLE_DOMAIN_EXAMPLES)
    elif strategy == "cross_domain":
        parts.append(CROSS_DOMAIN_EXAMPLES)
    parts.append(f"Question: {question}\nSQL:")
    return "\n\n".join(parts)


class Usage:
    def __init__(self):
        self.prompt = 0
        self.completion = 0

    def add(self, resp):
        if resp.usage:
            self.prompt += resp.usage.input_tokens
            self.completion += resp.usage.output_tokens

    def cost(self):
        return (self.prompt * PRICE_IN + self.completion * PRICE_OUT) / 1_000_000


def chat(client, model, system, user, usage):
    resp = client.responses.create(model=model, instructions=system, input=user)
    usage.add(resp)
    return resp.output_text.strip()


def clean_sql(text):
    text = re.sub(r"^```(?:sql)?\s*|\s*```$", "", text.strip(), flags=re.I)
    return text.strip().rstrip(";").strip()


def check_sql(sql):
    """Extra safety net. The real protection is the read-only database role."""
    if ";" in sql:
        return "Only a single statement is allowed."
    if not re.match(r"^(select|with)\b", sql, re.I):
        return "Only SELECT queries are allowed."
    if BAD_WORDS.search(sql):
        return "Query contains a disallowed keyword."
    return None


def run_sql(conn, sql):
    cur = conn.execute(sql)
    rows = cur.fetchmany(MAX_ROWS + 1)
    truncated = len(rows) > MAX_ROWS
    return rows[:MAX_ROWS], truncated


def ask(client, conn, schema, question, strategy, use_notes=True):
    usage = Usage()
    system = ("You are an expert PostgreSQL query writer. Reply with only the SQL query: "
              "no explanation, no markdown fences.")
    entry = {"time": datetime.now().isoformat(timespec="seconds"), "question": question,
             "strategy": strategy, "use_notes": use_notes, "sql": None, "success": False,
             "error": None}

    prompt = build_prompt(schema, question, strategy, use_notes)
    sql = clean_sql(chat(client, SQL_MODEL, system, prompt, usage))
    rows, truncated, error = None, False, None

    for attempt in range(2):  # one retry, feeding the error back to the model
        entry["sql"] = sql
        error = check_sql(sql)
        if not error:
            try:
                rows, truncated = run_sql(conn, sql)
                break
            except Exception as e:
                conn.rollback()
                error = str(e).strip().splitlines()[0]
        if attempt == 0:
            retry = (f"{prompt}\n{sql}\n\nThat query failed with this error: {error}\n"
                     "Write a corrected SQL query. Reply with only the SQL.")
            sql = clean_sql(chat(client, SQL_MODEL, system, retry, usage))

    if rows is None:
        entry["error"] = error
        answer = f"Sorry, I couldn't answer that. ({error})"
    else:
        data = json.dumps(rows, default=str)
        answer = chat(
            client, ANSWER_MODEL,
            "You answer questions about an event-services marketplace using only the data provided. "
            "Be concise and friendly. If there are no rows, say nothing matched. "
            "Do not invent facts that are not in the data.",
            f"Question: {question}\nSQL used: {sql}\nRows returned (JSON): {data}"
            + ("\nNote: results were cut off at the first 50 rows." if truncated else ""),
            usage)
        entry["success"] = True
        entry["row_count"] = len(rows)

    entry.update(retried=(attempt == 1), prompt_tokens=usage.prompt, completion_tokens=usage.completion,
                 est_cost_usd=round(usage.cost(), 6))
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry, answer, usage


def show(entry, answer, usage):
    print(f"\nSQL:\n{entry['sql']}\n")
    if entry["success"]:
        print(f"({entry['row_count']} rows)")
    print(f"\n{answer}\n")
    tokens = f"[{usage.prompt} prompt + {usage.completion} completion tokens"
    if PRICE_IN or PRICE_OUT:
        tokens += f", about ${usage.cost():.5f}"
    print(tokens + "]\n")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--strategy", choices=["zero_shot", "single_domain", "cross_domain"],
                   default="single_domain")
    p.add_argument("-q", "--question")
    p.add_argument("--no-notes", action="store_true",
                   help="leave the NOTES block out of the prompt (schema + examples only, like the paper)")
    args = p.parse_args()

    missing = [n for n, v in [("DATABASE_URL_READONLY", DB_URL), ("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY")),
                              ("OPENAI_MODEL", SQL_MODEL)] if not v]
    if missing:
        print("Missing in .env:", ", ".join(missing))
        return

    client = OpenAI()
    with psycopg.connect(DB_URL, row_factory=dict_row) as conn:
        schema = get_schema_text(conn)
        use_notes = not args.no_notes
        print(f"Strategy: {args.strategy}  |  Notes: {'on' if use_notes else 'off'}  |  Model: {SQL_MODEL}")
        if args.question:
            show(*ask(client, conn, schema, args.question, args.strategy, use_notes))
            return
        print("Ask a question about vendors, events, and bookings (type 'quit' to exit).")
        while True:
            q = input("\n> ").strip()
            if q.lower() in ("quit", "exit", "q"):
                break
            if q:
                show(*ask(client, conn, schema, q, args.strategy, use_notes))


if __name__ == "__main__":
    main()