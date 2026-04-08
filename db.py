import psycopg
from psycopg_pool import ConnectionPool
import logging
from dotenv import load_dotenv
import os

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")

logging.getLogger("psycopg").setLevel(logging.DEBUG)
logging.getLogger("psycopg.pool").setLevel(logging.INFO)


def create_connection_pool(
    db_host,
    db_name: str,
    user: str,
    password: str,
    min_size: int = 2,
    max_size: int = 10,
) -> ConnectionPool | None:
    """Opens a psycopg connection pool and returns it for use in other functions"""

    connection_string = (
        f"host={db_host} dbname={db_name} user={user} password={password}"
    )

    try:
        # Create a connection pool
        pool: ConnectionPool[psycopg.Connection[tuple]] = ConnectionPool(
            connection_string,
            min_size=min_size,
            max_size=max_size,
        )
        # Wait for it to be ready, before returning it
        pool.wait()
        return pool
    except Exception as e:
        logging.error(f"Error creating connection pool: {e}")
        return None


if __name__ == "__main__":
    load_dotenv()

    postgres_user = os.getenv("PG_USER", "postgres")
    postgres_db = os.getenv("DB_NAME", "postgres")
    postgres_host = os.getenv("DB_HOST", "localhost")
    postgres_password = os.getenv("PG_PASSWORD", "")

    pool = create_connection_pool(
        postgres_host, postgres_db, postgres_user, postgres_password
    )

    if pool is None:
        exit(1)

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT version()")
            for row in cur:
                print(row)
    pool.close()
