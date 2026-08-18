"""
semantic_matcher.py

Stage 1 of schema linking: semantic (embedding-based) table matching.
Replaces naive substring/lexical matching so the same code works against
ANY connected database, without maintaining a per-DB synonym dictionary.

"movie" -> "film", "actors" -> "actor" etc. work automatically because a
pretrained sentence embedding model already encodes that kind of semantic
similarity. Nothing is trained on your schema.

Feeds straight into your existing FK-traversal step (unchanged): just pass
the returned table list into it as the seed set.

Install:
    pip install sentence-transformers

First run downloads the model (~80MB) and needs internet once; after that
it works offline.

NOTE: This now takes the already-built `schema` dict (from
schema_introspect.get_schema()) instead of a live SQLAlchemy engine.
Previously it re-inspected the DB itself, which meant the DB got
introspected twice per run when used alongside hybrid_matcher.py --
once for `schema`, once here. Passing the dict in reuses the first
introspection instead of hitting the DB again.

NOTE 2 -- column-level matching, not table-blob matching:
Earlier this embedded each table as ONE string: table name + every
column name mashed together (e.g. "payment: payment_id, customer_id,
staff_id, rental_id, amount, payment_date, last_update"). That dilutes
the one column that might actually matter (e.g. "amount") into an
average alongside five unrelated ID/date columns, so a query like
"total revenue" scores the whole table too low even though "amount"
alone would've been a strong match.

Fix: embed the table name AND every column separately, score each
piece against the query independently, and give the table its single
best-scoring piece. This is still fully schema-agnostic -- no
per-domain vocabulary is injected anywhere. It works the same way on
Sakila ("revenue" ~ "amount") as it would on a hospital DB ("diagnosis"
~ "diagnosis_code") or any other domain, because it's purely a
resolution fix (comparing against one clean concept at a time instead
of a noisy blob), not injected domain knowledge.
"""

from collections import defaultdict
from sentence_transformers import SentenceTransformer, util


class SchemaEmbedder:
    def __init__(self, schema: dict, model_name="all-MiniLM-L6-v2", similarity_threshold=0.30):
        """
        schema: the schema dict from schema_introspect.get_schema().
            No DB connection needed here anymore -- table/column names
            are read straight out of this dict.
        similarity_threshold: minimum cosine similarity (0-1) for a
            table's BEST-scoring piece (its name or any one column) to
            count as a match. This is the ONLY filter (no top_k cap).
            Tune per DB -- scores depend on how descriptive your names
            are, and that varies by domain/schema, not just by DB size.
        """
        self.schema = schema
        self.model = SentenceTransformer(model_name)
        self.similarity_threshold = similarity_threshold
        # Each entry: (table_name, label) where label is either the
        # table name itself or "table.column" -- so a table-name match
        # (e.g. "movie" ~ "film") and a column match (e.g. "revenue" ~
        # "payment.amount") are both possible, independently.
        self._index: list[tuple[str, str]] = []
        self._embeddings = None
        self._build_embeddings()

    def _build_embeddings(self):
        """One-time cost per schema: embed the table name as its own
        item, plus every column as its own "table.column" item, so
        nothing gets diluted by averaging with unrelated columns."""
        texts = []

        for table, info in self.schema["tables"].items():
            self._index.append((table, table))
            texts.append(table)

            for col in info["columns"]:
                label = f"{table}.{col['name']}"
                self._index.append((table, label))
                texts.append(label.replace("_", " ").replace(".", " "))

        self._embeddings = self.model.encode(texts, convert_to_tensor=True)

    def match(self, query: str):
        """Return every table whose best-scoring piece (name or any
        column) clears similarity_threshold, ranked by that best score."""
        ranked = self.match_with_scores(query)

        matched = [
            table for table, score in ranked
            if score >= self.similarity_threshold
        ]

        # Safety net: never return zero tables if the DB has tables at
        # all -- fall back to the single best-scoring match rather than
        # letting the pipeline dead-end.
        if not matched and ranked:
            matched = [ranked[0][0]]

        return matched

    def match_with_scores(self, query: str):
        """Debug helper: ranked (table, best_score) list, where
        best_score is the highest similarity among that table's name
        and all its individual columns."""
        query_embedding = self.model.encode(query, convert_to_tensor=True)
        scores = util.cos_sim(query_embedding, self._embeddings)[0].tolist()

        best_per_table = defaultdict(lambda: float("-inf"))
        for (table, _label), score in zip(self._index, scores):
            if score > best_per_table[table]:
                best_per_table[table] = score

        return sorted(best_per_table.items(), key=lambda x: x[1], reverse=True)

    def match_with_column_detail(self, query: str):
        """Debug helper: for each table, which specific column (or the
        table name itself) drove its score -- useful for sanity-checking
        *why* a table matched, e.g. confirming 'payment' matched because
        of 'payment.amount' and not some unrelated column."""
        query_embedding = self.model.encode(query, convert_to_tensor=True)
        scores = util.cos_sim(query_embedding, self._embeddings)[0].tolist()

        best_per_table = {}
        for (table, label), score in zip(self._index, scores):
            if table not in best_per_table or score > best_per_table[table][1]:
                best_per_table[table] = (label, score)

        return sorted(best_per_table.items(), key=lambda x: x[1][1], reverse=True)


if __name__ == "__main__":
    from schema_introspect import get_schema

    schema = get_schema()
    embedder = SchemaEmbedder(schema)

    while True:
        query = input("\nEnter your natural language query (or 'exit'): ")
        if query.strip().lower() == "exit":
            break
        print("Matched tables:", embedder.match(query))
        print("Full ranking:", embedder.match_with_scores(query))