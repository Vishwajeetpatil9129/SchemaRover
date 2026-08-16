"""
Step: Schema Introspection
Reads a SQLite DB via SQLAlchemy and returns a structured schema dict.
"""

from sqlalchemy import create_engine, inspect


def get_schema(db_path: str = "mysql+pymysql://root:Vishwajeet%402005@127.0.0.1:3306/sakila") -> dict:

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