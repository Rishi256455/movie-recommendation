import os
import numpy as np
from fastembed import TextEmbedding
from rapidfuzz import process, fuzz, utils
from movies import MOVIES

MODEL_NAME = "BAAI/bge-small-en-v1.5"
CACHE_FILE = os.path.join(os.path.dirname(__file__), "embeddings.npy")
def _normalize(v):
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


class MovieEngine:
    def __init__(self):
        self.model = TextEmbedding(MODEL_NAME)
        self.titles = [m["title"] for m in MOVIES]
        self.vectors = self._load_or_build_vectors()

    def _load_or_build_vectors(self):
        # Reuse saved vectors if the movie list has not changed size
        if os.path.exists(CACHE_FILE):
            saved = np.load(CACHE_FILE)
            if saved.shape[0] == len(MOVIES):
                return saved
        # title + genres + overview -> one text per movie -> one vector per movie
        texts = [f'{m["title"]}. {", ".join(m["genres"])}. {m["overview"]}' for m in MOVIES]
        vectors = _normalize(np.array(list(self.model.embed(texts))))
        np.save(CACHE_FILE, vectors)
        return vectors

    def find_title(self, query, cutoff=82):
        """Exact or fuzzy title match. Returns the movie index or None."""
        hit = process.extractOne(query, self.titles, scorer=fuzz.ratio,
                                 processor=utils.default_process, score_cutoff=cutoff)
        return hit[2] if hit else None

    @staticmethod
    def _to_percent(score):
        # Cosine scores for this model sit roughly between 0.4 and 0.9; stretch to 0-99%
        return int(max(0, min(99, (score - 0.4) / 0.5 * 100)))

    def search(self, query, genres=None, top_k=10):
        """Returns (featured_movie_or_None, list_of_recommendations)."""
        query = query.strip()
        featured_idx = self.find_title(query)

        if featured_idx is not None:
            # Title typed: recommend movies similar to that movie
            q_vec = self.vectors[featured_idx]
        else:
            # Description typed: embed the query with the same model
            q_vec = _normalize(np.array(list(self.model.query_embed(query)))[0])

        scores = self.vectors @ q_vec  # cosine similarity (vectors are normalized)
        results = []
        for i in np.argsort(scores)[::-1]:
            if i == featured_idx:
                continue
            if genres and not set(genres) & set(MOVIES[i]["genres"]):
                continue
            results.append({**MOVIES[i], "match": self._to_percent(scores[i])})
            if len(results) == top_k:
                break

        featured = None
        if featured_idx is not None:
            featured = {**MOVIES[featured_idx], "match": 100}
        return featured, results