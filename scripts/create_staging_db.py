"""One-time script: create the `eve_staging` PostgreSQL database alongside
`neondb` on the existing Cloud SQL instance.

CREATE DATABASE cannot run inside a transaction, so we use autocommit. The
caller is responsible for authorizing the running machine's IP on the
Cloud SQL instance first — see `scripts/setup_staging_db.ps1`.

Idempotent: if `eve_staging` already exists, this exits 0 without error.
"""
import os
import sys


def main() -> int:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

    db_password = os.environ.get(
        'EVE_DB_PASSWORD',
        'N1Hdp7-v4QvOZ8HqvqNqDHGOWIX5-lZB',  # same value as prod DATABASE_URL
    )
    host = os.environ.get('EVE_DB_HOST', '136.114.114.44')  # eve-db public IP
    target_db = 'eve_staging'

    conn = psycopg2.connect(
        host=host, user='neondb_owner',
        password=db_password, dbname='neondb',  # connect to existing DB to issue CREATE
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (target_db,))
    if cur.fetchone():
        print(f"Database `{target_db}` already exists — nothing to do.")
        cur.close()
        conn.close()
        return 0

    print(f"Creating database `{target_db}` (owner=neondb_owner)…")
    cur.execute(f"CREATE DATABASE {target_db} OWNER neondb_owner")
    print("Created.")

    cur.close()
    conn.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
