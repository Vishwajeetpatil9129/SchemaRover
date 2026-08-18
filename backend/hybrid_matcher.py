"""
hybrid_matcher.py

Combines lexical_match.py and Semantic_matcher.py into a single
matching stage. Neither existing file's logic is changed -- this just
imports both and takes the union of their results.

Why union, not intersection: lexical catches exact/near-exact wording
cheaply and precisely; semantic catches synonyms lexical misses. Either
one finding a table is enough reason to include it as a seed -- FK
traversal (unchanged, downstream) handles further filtering/expansion.

Previously this built `schema` via get_schema() AND handed a live
engine to SchemaEmbedder, which re-inspected the DB a second time.
SchemaEmbedder now takes the schema dict directly, so the DB is only
introspected once per run, here.
"""

from lexical_match import lexical_match
from Semantic_matcher import SchemaEmbedder


def hybrid_match(nl_query: str, schema: dict, embedder: SchemaEmbedder) -> list[str]:
    """
    nl_query: the user's natural language query.
    schema: the schema dict from schema_introspect.get_schema().
    embedder: a SchemaEmbedder instance, built once from that same
        schema dict and reused across queries.

    Returns the union of lexical and semantic matches -- every table
    either method thinks is relevant.
    """
    lexical_results = set(lexical_match(nl_query, schema))
    semantic_results = set(embedder.match(nl_query))

    return list(lexical_results | semantic_results)


if __name__ == "__main__":
    from schema_introspect import get_schema

    schema = get_schema()          # introspected once
    embedder = SchemaEmbedder(schema)  # reuses it, no second DB hit

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