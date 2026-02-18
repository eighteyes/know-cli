"""
Semantic search indexing and querying for graph entities.
Provides TF-IDF based search with optional embedding support.

Responsibilities:
- Build and maintain search indices for graph content
- Execute semantic queries against indexed content
- Suggest related entities and dependency links
"""

import json
import math
import hashlib
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict, Counter
import re


class SearchIndex:
    """Build and manage search index for graph content."""

    def __init__(self, graph_path: str):
        """
        Initialize search index.

        Args:
            graph_path: Path to graph JSON file
        """
        self.graph_path = Path(graph_path)
        self.index_path = self._get_index_path()

    def _get_index_path(self) -> Path:
        """Get path to search index file."""
        # Store index next to graph file with -search-index.json suffix
        return self.graph_path.with_suffix('').with_suffix('.json').parent / \
            f"{self.graph_path.stem}-search-index.json"

    def _compute_graph_hash(self) -> str:
        """Compute SHA256 hash of graph file."""
        with open(self.graph_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()

    def is_stale(self) -> bool:
        """Check if index is stale compared to graph file."""
        if not self.index_path.exists():
            return True

        try:
            with open(self.index_path, 'r') as f:
                index_data = json.load(f)

            current_hash = self._compute_graph_hash()
            return index_data.get('graph_hash') != current_hash
        except (json.JSONDecodeError, KeyError):
            return True

    def ensure_fresh(self, use_embeddings: bool = False) -> None:
        """Rebuild index if stale."""
        if self.is_stale():
            self.build(use_embeddings=use_embeddings)

    def _extract_documents(self) -> List[Dict]:
        """
        Extract searchable documents from graph.

        Returns:
            List of documents with id, text, type, section
        """
        with open(self.graph_path, 'r') as f:
            graph_data = json.load(f)

        documents = []

        # Extract from entities
        entities = graph_data.get('entities', {})
        for entity_type, entity_list in entities.items():
            if isinstance(entity_list, dict):
                for entity_name, entity_data in entity_list.items():
                    if isinstance(entity_data, dict):
                        entity_id = f"{entity_type}:{entity_name}"
                        name = entity_data.get('name', entity_name)
                        description = entity_data.get('description', '')
                        text = f"{name} {description}"

                        documents.append({
                            'id': entity_id,
                            'text': text,
                            'type': entity_type,
                            'section': 'entities'
                        })

        # Extract from references
        references = graph_data.get('references', {})
        for ref_type, ref_list in references.items():
            if isinstance(ref_list, dict):
                for ref_name, ref_data in ref_list.items():
                    if isinstance(ref_data, dict):
                        ref_id = f"{ref_type}:{ref_name}"
                        # References may not have structured name/description
                        # Extract searchable text from all string values
                        text_parts = []
                        for value in ref_data.values():
                            if isinstance(value, str):
                                text_parts.append(value)

                        text = " ".join(text_parts)

                        documents.append({
                            'id': ref_id,
                            'text': text,
                            'type': ref_type,
                            'section': 'references'
                        })

        return documents

    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize text into words.

        Args:
            text: Input text

        Returns:
            List of lowercase tokens
        """
        # Split on whitespace and punctuation, convert to lowercase
        tokens = re.findall(r'\b\w+\b', text.lower())
        return tokens

    def _build_tfidf_index(self, documents: List[Dict]) -> Dict:
        """
        Build TF-IDF index from documents (pure Python).

        Args:
            documents: List of document dicts

        Returns:
            TF-IDF index data
        """
        # Build vocabulary and document frequencies
        vocabulary = set()
        doc_tokens = []

        for doc in documents:
            tokens = self._tokenize(doc['text'])
            doc_tokens.append(tokens)
            vocabulary.update(tokens)

        vocabulary = sorted(vocabulary)
        vocab_to_idx = {word: idx for idx, word in enumerate(vocabulary)}

        # Compute IDF (inverse document frequency)
        doc_count = len(documents)
        word_doc_count = Counter()

        for tokens in doc_tokens:
            unique_tokens = set(tokens)
            for token in unique_tokens:
                word_doc_count[token] += 1

        idf = {}
        for word in vocabulary:
            # IDF = log(N / (1 + df))
            idf[word] = math.log(doc_count / (1 + word_doc_count[word]))

        # Compute TF-IDF vectors for each document
        vectors = {}

        for doc, tokens in zip(documents, doc_tokens):
            # Compute term frequencies
            tf = Counter(tokens)
            total_terms = len(tokens)

            # Compute TF-IDF vector (sparse representation)
            vector = {}
            for word, count in tf.items():
                # TF = count / total_terms
                tf_val = count / total_terms if total_terms > 0 else 0
                tfidf_val = tf_val * idf[word]

                if tfidf_val > 0:
                    vector[word] = tfidf_val

            vectors[doc['id']] = vector

        return {
            'vocabulary': vocab_to_idx,
            'idf': idf,
            'vectors': vectors
        }

    def _build_embedding_index(self, documents: List[Dict]) -> Optional[Dict]:
        """
        Build embedding index (requires LLM provider).

        Args:
            documents: List of document dicts

        Returns:
            Embedding index data or None if not available
        """
        # TODO: Phase 4 - implement embedding support via LLMProvider
        return None

    def build(self, use_embeddings: bool = False) -> None:
        """
        Build search index from graph.

        Args:
            use_embeddings: Use embeddings if available
        """
        # Extract documents
        documents = self._extract_documents()

        # Build TF-IDF index
        tfidf_index = self._build_tfidf_index(documents)

        # Build embedding index if requested
        embeddings_index = None
        if use_embeddings:
            embeddings_index = self._build_embedding_index(documents)

        # Save index
        index_data = {
            'version': 1,
            'method': 'embeddings' if embeddings_index else 'tfidf',
            'graph_hash': self._compute_graph_hash(),
            'documents': documents,
            'tfidf': tfidf_index,
            'embeddings': embeddings_index
        }

        with open(self.index_path, 'w') as f:
            json.dump(index_data, f, indent=2)

    def load(self) -> Dict:
        """Load index from disk."""
        with open(self.index_path, 'r') as f:
            return json.load(f)


class SemanticSearcher:
    """Query search index for semantic matches."""

    def __init__(self, search_index: SearchIndex):
        """
        Initialize semantic searcher.

        Args:
            search_index: SearchIndex instance
        """
        self.index = search_index
        self._index_data = None

    def _ensure_index(self) -> None:
        """Ensure index is loaded."""
        if self._index_data is None:
            self.index.ensure_fresh()
            self._index_data = self.index.load()

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize query text (same as index tokenization)."""
        tokens = re.findall(r'\b\w+\b', text.lower())
        return tokens

    def _compute_query_vector(self, query: str) -> Dict[str, float]:
        """
        Compute TF-IDF vector for query.

        Args:
            query: Query string

        Returns:
            Sparse TF-IDF vector
        """
        self._ensure_index()

        tokens = self._tokenize(query)
        tf = Counter(tokens)
        total_terms = len(tokens)

        # Get IDF values from index
        idf = self._index_data['tfidf']['idf']

        # Compute TF-IDF for query
        vector = {}
        for word, count in tf.items():
            if word in idf:
                tf_val = count / total_terms if total_terms > 0 else 0
                tfidf_val = tf_val * idf[word]
                if tfidf_val > 0:
                    vector[word] = tfidf_val

        return vector

    def _cosine_similarity(self, vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
        """
        Compute cosine similarity between two sparse vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Similarity score (0-1)
        """
        # Compute dot product
        dot_product = 0.0
        for word in vec1:
            if word in vec2:
                dot_product += vec1[word] * vec2[word]

        # Compute magnitudes
        mag1 = math.sqrt(sum(v * v for v in vec1.values()))
        mag2 = math.sqrt(sum(v * v for v in vec2.values()))

        # Avoid division by zero
        if mag1 == 0 or mag2 == 0:
            return 0.0

        return dot_product / (mag1 * mag2)

    def find(
        self,
        query: str,
        limit: int = 10,
        threshold: float = 0.3,
        section: str = 'all'
    ) -> List[Dict]:
        """
        Find entities matching query semantically.

        Args:
            query: Search query
            limit: Maximum results to return
            threshold: Minimum similarity score (0-1)
            section: Filter by section ('all', 'entities', 'references')

        Returns:
            List of results with id, score, text, type, section
        """
        self._ensure_index()

        # Compute query vector
        query_vector = self._compute_query_vector(query)

        # Get document vectors
        doc_vectors = self._index_data['tfidf']['vectors']
        documents = {doc['id']: doc for doc in self._index_data['documents']}

        # Compute similarities
        results = []
        for doc_id, doc_vector in doc_vectors.items():
            doc = documents[doc_id]

            # Filter by section
            if section != 'all' and doc['section'] != section:
                continue

            # Compute similarity
            score = self._cosine_similarity(query_vector, doc_vector)

            if score >= threshold:
                results.append({
                    'id': doc_id,
                    'score': score,
                    'text': doc['text'],
                    'type': doc['type'],
                    'section': doc['section']
                })

        # Sort by score descending
        results.sort(key=lambda x: x['score'], reverse=True)

        return results[:limit]

    def related(
        self,
        entity_id: str,
        limit: int = 10,
        include_graph_proximity: bool = True
    ) -> List[Dict]:
        """
        Find entities related to given entity.

        Args:
            entity_id: Entity to find related items for
            limit: Maximum results
            include_graph_proximity: Weight by graph distance

        Returns:
            List of related entities with scores
        """
        self._ensure_index()

        # Get entity's text as query
        documents = {doc['id']: doc for doc in self._index_data['documents']}

        if entity_id not in documents:
            return []

        entity_doc = documents[entity_id]
        query_text = entity_doc['text']

        # Find similar entities
        results = self.find(query_text, limit=limit * 2, threshold=0.1)

        # Filter out the query entity itself
        results = [r for r in results if r['id'] != entity_id]

        # TODO: Phase 5 - add graph proximity scoring

        return results[:limit]

