"""
DuckDB module
"""

import os

from tempfile import TemporaryDirectory

# Conditional import
try:
    import duckdb

    DUCKDB = True
except ImportError:
    DUCKDB = False

from .embedded import Embedded
from .schema import Statement


class DuckDB(Embedded):
    """
    Database instance backed by DuckDB.
    """

    # Delete single document and object
    DELETE_DOCUMENT = "DELETE FROM documents WHERE id = ?"
    DELETE_OBJECT = "DELETE FROM objects WHERE id = ?"

    def __init__(self, config):
        super().__init__(config)

        if not DUCKDB:
            raise ImportError('DuckDB is not available - install "database" extra to enable')

    def insertdocument(self, uid, data, tags, entry):
        # Delete existing document
        self.cursor.execute(DuckDB.DELETE_DOCUMENT, [uid])

        # Call parent logic
        super().insertdocument(uid, data, tags, entry)

    def insertobject(self, uid, data, tags, entry):
        # Delete existing object
        self.cursor.execute(DuckDB.DELETE_OBJECT, [uid])

        # Call parent logic
        super().insertobject(uid, data, tags, entry)

    def connect(self, path=":memory:"):
        # Create connection and start a transaction
        # pylint: disable=I1101
        connection = duckdb.connect(path)
        connection.begin()

        return connection

    def getcursor(self):
        return self.connection

    def rows(self):
        # Iteratively retrieve and yield rows
        batch = 256
        rows = self.cursor.fetchmany(batch)
        while rows:
            yield from rows
            rows = self.cursor.fetchmany(batch)

    def addfunctions(self):
        # DuckDB doesn't currently support scalar functions
        return

    def copy(self, path):
        # Delete existing file, if necessary
        if os.path.exists(path):
            os.remove(path)

        # Create database connection
        # pylint: disable=I1101
        connection = duckdb.connect(path)

        # List of tables
        tables = ["documents", "objects", "sections"]

        with TemporaryDirectory() as directory:
            # Export existing tables
            for table in tables:
                self.connection.execute(f"COPY {table} TO '{directory}/{table}.parquet' (FORMAT parquet)")

            # Create initial schema
            for schema in [Statement.CREATE_DOCUMENTS, Statement.CREATE_OBJECTS, Statement.CREATE_SECTIONS % "sections"]:
                connection.execute(schema)

            # Import tables into new schema
            for table in tables:
                connection.execute(f"COPY {table} FROM '{directory}/{table}.parquet' (FORMAT parquet)")

            # Create indexes and sync data to database file
            connection.execute(Statement.CREATE_SECTIONS_INDEX)
            connection.execute("CHECKPOINT")

        # Start transaction
        connection.begin()

        return connection
