"""
hybrid_matcher.py

Combines lexical_matcher.py and semantic_matcher.py into a single
matching stage. Neither existing file is modified -- this just imports
both and takes the union of their results.

Why union, not intersection: lexical catches exact/near-exact wording
cheaply and precisely; semantic catches synonyms lexical misses. Either
one finding a table is enough reason to include it as a seed -- FK
traversal (unchanged, downstream) handles further filtering/expansion.
"""

from lexical_match import lexical_match
from Semantic_matcher import SchemaEmbedder


def hybrid_match(nl_query: str, schema: dict, embedder: SchemaEmbedder) -> list[str]:
    """
    nl_query: the user's natural language query.
    schema: the schema dict from schema_introspect.get_schema()
        (same thing you already pass into lexical_match).
    embedder: a SchemaEmbedder instance, built once per DB connection
        (same engine as the one schema/get_schema() used).

    Returns the union of lexical and semantic matches -- every table
    either method thinks is relevant.
    """
    lexical_results = set(lexical_match(nl_query, schema))
    semantic_results = set(embedder.match(nl_query))

    return list(lexical_results | semantic_results)


if __name__ == "__main__":
    from sqlalchemy import create_engine
    from schema_introspect import get_schema

    # Swap for your actual DB URL.
    engine = create_engine("mysql+pymysql://root:Vishwajeet%402005@127.0.0.1:3306/sakila")

    schema = get_schema()
    embedder = SchemaEmbedder(engine)  # built once, reused across queries

    while True:
        query = input("\nEnter your natural language query (or 'exit'): ")
        if query.strip().lower() == "exit":
            break

        lexical_only = set(lexical_match(query, schema))
        semantic_only = set(embedder.match(query))
        combined = hybrid_match(query, schema, embedder)

        print(f"\nQuery: {query}")
        print(f"Lexical matched:  {sorted(lexical_only)}")
        print(f"Semantic matched: {sorted(semantic_only)}")
        print(f"Hybrid (union):   {sorted(combined)}")