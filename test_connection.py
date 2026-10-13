"""Checks that both database logins work and that ai_readonly cannot write.

Nothing is saved: the admin write test is rolled back.
"""
import os

import psycopg
from dotenv import load_dotenv

load_dotenv()

ADMIN_URL = os.getenv("DATABASE_URL_ADMIN")
READONLY_URL = os.getenv("DATABASE_URL_READONLY")


def check(label, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {label}" + (f"  ({detail})" if detail else ""))


def main():
    if not ADMIN_URL or not READONLY_URL:
        print("Missing DATABASE_URL_ADMIN or DATABASE_URL_READONLY in .env")
        return

    # --- Admin (postgres) ---
    try:
        with psycopg.connect(ADMIN_URL) as conn:
            tables = conn.execute(
                "SELECT count(*) FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_type = 'BASE TABLE'"
            ).fetchone()[0]
            check("Admin can connect", True)
            check("Schema has 8 tables", tables == 8, f"found {tables}")

            # Write test, rolled back so nothing is saved
            try:
                conn.execute("INSERT INTO categories (name) VALUES ('__test__')")
                check("Admin can write", True)
            finally:
                conn.rollback()
    except Exception as e:
        check("Admin connection", False, str(e).splitlines()[0])

    # --- Read-only (ai_readonly) ---
    try:
        with psycopg.connect(READONLY_URL) as conn:
            check("Read-only can connect", True)

            try:
                conn.execute("SELECT count(*) FROM vendors").fetchone()
                check("Read-only can read tables", True)
            except Exception as e:
                check("Read-only can read tables", False, str(e).splitlines()[0])
                conn.rollback()

            try:
                conn.execute("INSERT INTO categories (name) VALUES ('__test__')")
                check("Read-only is blocked from writing", False, "the write succeeded!")
            except Exception as e:
                check("Read-only is blocked from writing", True, str(e).splitlines()[0])
            finally:
                conn.rollback()
    except Exception as e:
        check("Read-only connection", False, str(e).splitlines()[0])


if __name__ == "__main__":
    main()