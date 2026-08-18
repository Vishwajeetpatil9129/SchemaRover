"""
Step: Schema Introspection
Reads a DB via SQLAlchemy and returns a structured schema dict.

DB connection string is read from the DB_URL environment variable
(see .env.example) instead of being hardcoded, so credentials never
end up in source control.
"""
from dotenv import load_dotenv
load_dotenv()

import os
from sqlalchemy import create_engine, inspect

def get_db_url() -> str:
    return os.environ.get("DB_URL")


def get_schema(db_path: str | None = None) -> dict:
    """
    db_path: optional explicit SQLAlchemy connection string. If omitted,
    falls back to the DB_URL environment variable, then DEFAULT_DB_URL.
    """
    db_path = db_path or get_db_url()

    engine = create_engine(db_path)
    inspector = inspect(engine)

    schema = {"tables": {}}

    for table_name in inspector.get_table_names():
        columns = [
            {"name": col["name"], "type": str(col["type"])}
            for col in inspector.get_columns(table_name)
        ]

        pk_constraint = inspector.get_pk_constraint(table_name)
        primary_key = pk_constraint.get("constrained_columns", [])

        foreign_keys = []
        for fk in inspector.get_foreign_keys(table_name):
            foreign_keys.append({
                "column": fk["constrained_columns"][0],
                "ref_table": fk["referred_table"],
                "ref_column": fk["referred_columns"][0],
            })

        schema["tables"][table_name] = {
            "columns": columns,
            "primary_key": primary_key,
            "foreign_keys": foreign_keys,
        }

    return schema


if __name__ == "__main__":
    import json
    schema = get_schema()
    print(json.dumps(schema, indent=2))
