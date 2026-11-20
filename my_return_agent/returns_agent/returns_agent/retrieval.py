"""RAG: finds the 3 best passages in the handbook or the catalog.

    1. Indexing  (once, when the app starts):  every paragraph is stored twice, by meaning and by exact words
    2. Searching (every time the tool is called):  meaning search + word search -> merge (RRF) -> rerank -> best 3
"""

from fastembed.rerank.cross_encoder import TextCrossEncoder
from qdrant_client import QdrantClient, models

qdrant = QdrantClient(":memory:")                                # the vector database, in memory
reranker = TextCrossEncoder("Xenova/ms-marco-MiniLM-L-6-v2")     # scores how well a passage answers a question


# Turns text into a "meaning" vector: "send back" matches "return"
def by_meaning(text):
    return models.Document(text=text, model="BAAI/bge-small-en-v1.5")


# Turns text into a "words" vector (BM25): "ZT-55U5" matches only "ZT-55U5"
def by_words(text):
    return models.Document(text=text, model="Qdrant/bm25")


# ======================================== 1. INDEXING

# Stores every paragraph of one file in its own collection: "handbook" or "catalog"
def add_file(name):

    # Step 1: create an empty collection that can hold both kinds of vectors
    qdrant.create_collection(
        name,
        vectors_config={"meaning": models.VectorParams(size=384, distance=models.Distance.COSINE)},
        sparse_vectors_config={"words": models.SparseVectorParams(modifier=models.Modifier.IDF)},
    )

    # Step 2: read the file and split it into paragraphs (one blank line = a new paragraph)
    text = open(f"knowledge/{name}.txt").read()
    paragraphs = []
    for part in text.split("\n\n"):
        if part.strip() != "":
            paragraphs.append(part.strip())

    # Step 3: store each paragraph with its two vectors, and keep the text with it
    for number, paragraph in enumerate(paragraphs):
        point = models.PointStruct(
            id=number,
            vector={"meaning": by_meaning(paragraph), "words": by_words(paragraph)},
            payload={"text": paragraph},
        )
        qdrant.upsert(name, [point])


add_file("handbook")
add_file("catalog")


# ======================================== 2. SEARCHING

# Finds the 3 best passages for the question in one collection: "handbook" or "catalog"
def search(query, source):

    # Step 1: search by meaning (10 results)
    meaning_search = models.Prefetch(query=by_meaning(query), using="meaning", limit=10)

    # Step 2: search by exact words (10 results)
    words_search = models.Prefetch(query=by_words(query), using="words", limit=10)

    # Step 3: Qdrant runs both searches first ("prefetch"), then merges them into one top 10 with RRF
    result = qdrant.query_points(
        source,
        prefetch=[meaning_search, words_search],
        query=models.RrfQuery(rrf=models.Rrf(k=60)),     # RRF: a passage ranked high in both lists comes first
        limit=10,
    )
    top_10 = []
    for point in result.points:
        top_10.append(point.payload["text"])

    # Step 4: rerank: give each of the 10 a score for how well it answers the question
    scores = list(reranker.rerank(query, top_10))

    # Step 5: keep the 3 passages with the highest scores
    scored = []
    for i in range(len(top_10)):
        scored.append((scores[i], top_10[i]))
    scored.sort(reverse=True)               # highest score first
    best_3 = scored[:3]

    # Step 6: join the 3 passages into one text for the LLM
    answer = ""
    for score, passage in best_3:
        answer += passage + "\n\n"
    return answer.strip()