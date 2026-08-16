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
"""

from sentence_transformers import SentenceTransformer, util
from sqlalchemy import inspect


class SchemaEmbedder:
    def __init__(self, engine, model_name="all-MiniLM-L6-v2", similarity_threshold=0.30):
        """
        engine: a SQLAlchemy engine, already connected to the target DB.
        similarity_threshold: minimum cosine similarity (0-1) to count as
            a match. This is now the ONLY filter (no top_k cap) -- every
            table scoring at or above this is returned. Lower = more
            permissive (more false positives, but less risk of missing a
            real match like a bridge table); higher = stricter.
            0.15 is a starting point based on Sakila testing -- tune
            against a few real queries on your own DB, since scores
            depend on how descriptive your table/column names are.
        """
        self.engine = engine
        self.model = SentenceTransformer(model_name)
        self.similarity_threshold = similarity_threshold
        self._table_names = []
        self._column_map = {}
        self._table_embeddings = None
        self._build_schema_embeddings()

    def _build_schema_embeddings(self):
        """One-time cost per DB connection: embed every table using its
        name plus its column names as context, so a query mentioning a
        column (e.g. 'salary') can still surface the right table even if
        the table name itself ('employees') isn't mentioned."""
        inspector = inspect(self.engine)
        self._table_names = inspector.get_table_names()

        texts = []
        for table in self._table_names:
            columns = [col["name"] for col in inspector.get_columns(table)]
            self._column_map[table] = columns
            texts.append(f"{table}: {', '.join(columns)}")

        self._table_embeddings = self.model.encode(texts, convert_to_tensor=True)

    def match(self, query: str):
        """Return every table scoring at or above similarity_threshold,
        ranked by relevance. No top_k cap -- the threshold is the only
        filter, so this returns as many or as few tables as genuinely
        clear the bar."""
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
        """Debug helper: full ranked (table, similarity_score) list."""
        query_embedding = self.model.encode(query, convert_to_tensor=True)
        scores = util.cos_sim(query_embedding, self._table_embeddings)[0]
        return sorted(
            zip(self._table_names, scores.tolist()),
            key=lambda x: x[1],
            reverse=True,
        )


if __name__ == "__main__":
    from sqlalchemy import create_engine

    # Swap this for whichever DB you're testing against right now.
    engine = create_engine("mysql+pymysql://root:Vishwajeet%402005@127.0.0.1:3306/sakila")
    embedder = SchemaEmbedder(engine)

    while True:
        query = input("\nEnter your natural language query (or 'exit'): ")
        if query.strip().lower() == "exit":
            break
        print("Matched tables:", embedder.match(query))
        print("Full ranking:", embedder.match_with_scores(query))