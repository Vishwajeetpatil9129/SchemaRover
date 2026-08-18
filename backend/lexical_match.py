"""
Step: Lexical Matching
Given an NL query and the schema dict from schema_introspect.py,
find which tables/columns are likely relevant by keyword overlap.
(Unchanged -- included here just so the backend/ folder is complete.)
"""

import re


def tokenize(text: str) -> list[str]:
    """Lowercase and split into word tokens, stripping punctuation."""
    text = text.lower()
    tokens = re.findall(r"[a-z0-9_]+", text)
    return tokens


def lexical_match(nl_query: str, schema: dict) -> list[str]:
    """
    Returns a list of table names that match tokens in the NL query,
    either by table name or by one of their column names.
    """
    query_tokens = set(tokenize(nl_query))
    matched_tables = set()

    for table_name, table_info in schema["tables"].items():
        table_tokens = set(tokenize(table_name))
        # singular/plural loose match: "employee" should match "employees"
        table_tokens_stripped = {t.rstrip("s") for t in table_tokens}

        if query_tokens & table_tokens or query_tokens & table_tokens_stripped:
            matched_tables.add(table_name)
            continue

        # check column names too
        for col in table_info["columns"]:
            col_tokens = set(tokenize(col["name"]))
            if query_tokens & col_tokens:
                matched_tables.add(table_name)
                break

    return list(matched_tables)


if __name__ == "__main__":
    from schema_introspect import get_schema

    schema = get_schema()

    while True:
        q = input("\nEnter your natural language query (or type 'exit' to quit): ")

        if q.lower() == "exit":
            print("Exiting...")
            break

        matched = lexical_match(q, schema)

        print(f"\nQuery: {q}")
        print(f"Matched tables: {matched}")