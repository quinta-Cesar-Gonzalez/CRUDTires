import os
import re
from typing import Optional, List
from contextlib import contextmanager
import pymysql
from pymysql import cursors


def parse_mysql_uri(uri: str) -> dict:
    """Parse MySQL URI into connection parameters."""
    # Format: mysql+mysqlconnector://user:pass@host:port/database
    pattern = r'mysql\+mysqlconnector://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)'
    match = re.match(pattern, uri)
    
    if not match:
        raise ValueError('Invalid MySQL URI format')
    
    return {
        'user': match.group(1),
        'password': match.group(2),
        'host': match.group(3),
        'port': int(match.group(4)),
        'database': match.group(5)
    }


# Parse connection config
MYSQL_URI = os.getenv('MYSQL_URI')
if not MYSQL_URI:
    raise ValueError('MYSQL_URI environment variable is required')

db_config = parse_mysql_uri(MYSQL_URI)


# Connection pool configuration optimized for Lambda
connection_config = {
    **db_config,
    'cursorclass': cursors.DictCursor,
    'connect_timeout': 10,
    'autocommit': True,
}


@contextmanager
def get_connection():
    """Get a database connection with automatic cleanup."""
    connection = None
    try:
        connection = pymysql.connect(**connection_config)
        yield connection
    finally:
        if connection:
            connection.close()


def query(sql: str, params: tuple = None) -> List[dict]:
    """Execute a SELECT query and return all results."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            return cursor.fetchall()


def query_one(sql: str, params: tuple = None) -> Optional[dict]:
    """Execute a SELECT query and return one result."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            return cursor.fetchone()


def execute(sql: str, params: tuple = None) -> int:
    """Execute an INSERT/UPDATE/DELETE query and return affected rows or last insert id."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            # Return lastrowid for INSERT, rowcount for UPDATE/DELETE
            return cursor.lastrowid if cursor.lastrowid else cursor.rowcount
