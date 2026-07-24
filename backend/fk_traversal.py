"""
Step: FK Graph Traversal
Given the lexically matched tables, expand the set by walking the
foreign key graph so that join-connector tables are included even
if they weren't mentioned by name in the NL query.
"""

from collections import defaultdict


def build_fk_graph(schema: dict) -> dict:
    """
    Builds an undirected adjacency list: table -> set of directly
    connected tables (via FK in either direction).
    """
    graph = defaultdict(set)

    for table_name, table_info in schema["tables"].items():
        for fk in table_info["foreign_keys"]:
            ref_table = fk["ref_table"]
            graph[table_name].add(ref_table)
            graph[ref_table].add(table_name)

    return graph


def expand_with_fk_traversal(matched_tables: list[str], schema: dict, max_hops: int = 1) -> list[str]:
    """
    Starting from matched_tables, walk the FK graph up to max_hops
    steps to pull in connecting tables (e.g. junction tables like
    'assignments' that link employees <-> projects).
    """
    graph = build_fk_graph(schema)
    result = set(matched_tables)

    frontier = set(matched_tables)
    for _ in range(max_hops):
        next_frontier = set()
        for table in frontier:
            neighbors = graph.get(table, set())
            next_frontier |= neighbors
        result |= next_frontier
        frontier = next_frontier

    return list(result)


if __name__ == "__main__":
    from schema_introspect import get_schema
    from lexical_match import lexical_match

    schema = get_schema()

    test_queries = [
        "show employees and their project hours",
        "list all employees with their salary",
        "which clients are linked to which departments",
    ]

    for q in test_queries:
        lexical_matches = lexical_match(q, schema)
        expanded = expand_with_fk_traversal(lexical_matches, schema, max_hops=1)
        print(f"Query: {q}")
        print(f"Lexical matches: {lexical_matches}")
        print(f"After FK expansion: {expanded}\n")