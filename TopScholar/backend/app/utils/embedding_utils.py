import numpy as np
import json
import re
from typing import List, Optional
from app.config import settings

_embeddings_cache = {}
_model = None


class SimpleEmbeddingService:
    """轻量级向量化服务 (开发环境使用 TF-IDF + numpy cosine)"""

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return re.findall(r'\b\w+\b', text.lower())

    @staticmethod
    def _build_vocab(documents: List[str]) -> dict:
        vocab = {}
        for doc in documents:
            for token in SimpleEmbeddingService._tokenize(doc):
                vocab[token] = vocab.get(token, 0) + 1
        sorted_vocab = sorted(vocab.items(), key=lambda x: -x[1])
        return {word: idx for idx, (word, _) in enumerate(sorted_vocab)}

    @staticmethod
    def _tfidf_vector(text: str, vocab: dict, idf: dict) -> List[float]:
        tokens = SimpleEmbeddingService._tokenize(text)
        if not tokens:
            return [0.0] * len(vocab)
        tf = {}
        for t in tokens:
            tf[t] = tf.get(t, 0) + 1
        max_tf = max(tf.values())
        vec = [0.0] * len(vocab)
        for word, idx in vocab.items():
            if word in tf:
                vec[idx] = (1 + np.log(tf[word]) / (1 + np.log(max_tf))) * idf.get(word, 0)
        norm = np.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec

    @staticmethod
    def build_corpus(documents: List[str]):
        N = len(documents)
        vocab = SimpleEmbeddingService._build_vocab(documents)
        idf = {}
        for word in vocab:
            df = sum(1 for doc in documents if word in SimpleEmbeddingService._tokenize(doc))
            idf[word] = np.log((N + 1) / (df + 1)) + 1
        _embeddings_cache['vocab'] = vocab
        _embeddings_cache['idf'] = idf

    @staticmethod
    def generate_embedding(text: str) -> List[float]:
        if 'vocab' not in _embeddings_cache:
            return [0.0] * settings.EMBEDDING_DIM
        vocab = _embeddings_cache['vocab']
        idf = _embeddings_cache['idf']
        vec = SimpleEmbeddingService._tfidf_vector(text, vocab, idf)
        if len(vec) < settings.EMBEDDING_DIM:
            vec.extend([0.0] * (settings.EMBEDDING_DIM - len(vec)))
        return vec[:settings.EMBEDDING_DIM]

    @staticmethod
    def cosine_similarity(a: List[float], b: List[float]) -> float:
        a_arr = np.array(a)
        b_arr = np.array(b)
        dot = np.dot(a_arr, b_arr)
        norm_a = np.linalg.norm(a_arr)
        norm_b = np.linalg.norm(b_arr)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(dot / (norm_a * norm_b))

    @staticmethod
    def save_embedding(text: str) -> str:
        vec = SimpleEmbeddingService.generate_embedding(text)
        return json.dumps(vec)

    @staticmethod
    def load_embedding(text: str) -> List[float]:
        try:
            return json.loads(text)
        except (json.JSONDecodeError, TypeError):
            return [0.0] * settings.EMBEDDING_DIM


embedding_service = SimpleEmbeddingService()
