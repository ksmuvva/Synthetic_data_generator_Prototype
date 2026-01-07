"""
Database output format for synthetic data.

Provides database export capabilities for synthetic data.
"""

import pandas as pd
from pathlib import Path
from typing import Optional


class DatabaseGenerator:
    """Generate database table output."""

    def __init__(
        self,
        connection_string: Optional[str] = None,
        db_type: str = "sqlite",
    ):
        """
        Initialize generator.

        Args:
            connection_string: Database connection string
            db_type: Database type (sqlite, postgresql, mysql)
        """
        self.connection_string = connection_string
        self.db_type = db_type

    def generate(
        self,
        df: pd.DataFrame,
        output_path: str,
        table_name: str,
        if_exists: str = "replace",
    ) -> str:
        """
        Generate database table.

        Args:
            df: Dataframe to export
            output_path: Database file path or connection info
            table_name: Name of table to create
            if_exists: What to do if table exists

        Returns:
            Path/connection string
        """
        if self.db_type == "sqlite":
            return self._generate_sqlite(df, output_path, table_name, if_exists)
        else:
            return self._generate_generic(df, table_name, if_exists)

    def _generate_sqlite(
        self, df: pd.DataFrame, output_path: str, table_name: str, if_exists: str
    ) -> str:
        """Generate SQLite database."""
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        conn_str = f"sqlite:///{output}"
        df.to_sql(table_name, conn_str, if_exists=if_exists, index=False)

        return str(output)

    def _generate_generic(self, df: pd.DataFrame, table_name: str, if_exists: str) -> str:
        """Generate using SQLAlchemy connection."""
        if self.connection_string:
            df.to_sql(
                table_name,
                self.connection_string,
                if_exists=if_exists,
                index=False,
            )
            return self.connection_string
        else:
            raise ValueError("Connection string required for non-SQLite databases")
