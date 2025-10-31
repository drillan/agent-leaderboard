"""DuckDB connection management and database initialization.

This module provides connection management for DuckDB and handles
database schema initialization and migration.
"""

from pathlib import Path

import duckdb

from .schema import ALL_DDL_STATEMENTS, SCHEMA_VERSION


class DatabaseConnection:
    """Manages DuckDB database connection and initialization.

    Attributes:
        db_path: Path to the DuckDB database file
        conn: Active DuckDB connection
    """

    def __init__(self, db_path: str | Path) -> None:
        """Initialize database connection.

        Args:
            db_path: Path to the DuckDB database file
        """
        self.db_path = Path(db_path)
        self.conn: duckdb.DuckDBPyConnection | None = None

    def connect(self) -> duckdb.DuckDBPyConnection:
        """Establish connection to the database.

        Returns:
            Active DuckDB connection

        Raises:
            duckdb.Error: If connection fails
        """
        if self.conn is None:
            self.conn = duckdb.connect(str(self.db_path))
        return self.conn

    def close(self) -> None:
        """Close the database connection."""
        if self.conn is not None:
            self.conn.close()
            self.conn = None

    def initialize_schema(self) -> None:
        """Initialize database schema by executing all DDL statements.

        This method:
        1. Creates the schema_metadata table
        2. Checks the current schema version
        3. Executes all DDL statements if schema is new or needs update
        4. Records the schema version

        Raises:
            duckdb.Error: If schema initialization fails
        """
        conn = self.connect()

        # Execute all DDL statements
        for ddl in ALL_DDL_STATEMENTS:
            conn.execute(ddl)

        # Check if schema version is already recorded
        result = conn.execute(
            "SELECT version FROM schema_metadata WHERE version = ?", [SCHEMA_VERSION]
        ).fetchone()

        if result is None:
            # Record schema version
            conn.execute(
                "INSERT INTO schema_metadata (version) VALUES (?)", [SCHEMA_VERSION]
            )

        conn.commit()

    def __enter__(self) -> duckdb.DuckDBPyConnection:
        """Context manager entry.

        Returns:
            Active DuckDB connection
        """
        return self.connect()

    def __exit__(self, exc_type: type, exc_val: Exception, exc_tb: object) -> None:
        """Context manager exit.

        Args:
            exc_type: Exception type
            exc_val: Exception value
            exc_tb: Exception traceback
        """
        self.close()


def get_connection(db_path: str | Path) -> DatabaseConnection:
    """Create a new database connection instance.

    Args:
        db_path: Path to the DuckDB database file

    Returns:
        DatabaseConnection instance
    """
    return DatabaseConnection(db_path)


def initialize_database(db_path: str | Path) -> None:
    """Initialize a new database with the current schema.

    Args:
        db_path: Path to the DuckDB database file

    Raises:
        duckdb.Error: If initialization fails
    """
    db_conn = DatabaseConnection(db_path)
    db_conn.initialize_schema()
    db_conn.close()
