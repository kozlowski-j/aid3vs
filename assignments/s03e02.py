from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from openai import OpenAI
from utils import read_txt_files, post_json_data_to_url
from dotenv import load_dotenv
import os
import uuid

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_PROJECT_ID = os.getenv("OPENAI_PROJECT_ID")
OPENAI_ORGANIZATION_ID = os.getenv("OPENAI_ORGANIZATION_ID")
CENTRALA_BASE_URL = os.getenv("CENTRALA_BASE_URL")
AIDEVS_MY_APIKEY = os.getenv("AIDEVS_MY_APIKEY")

openai_client = OpenAI(
    organization=OPENAI_ORGANIZATION_ID,
    project=OPENAI_PROJECT_ID,
    api_key=OPENAI_API_KEY,
)

# Initialize Qdrant client
qdrant_client = QdrantClient(host="localhost", port=6333)

# Create a collection if it doesn't exist
collection_name = "aidevs-s03e02"
if not qdrant_client.collection_exists(collection_name):
    qdrant_client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
    )

# Function to get embedding from OpenAI
def get_embedding(txt, size, model="text-embedding-3-large"):
    txt = txt.replace("\n", " ")
    return openai_client.embeddings.create(input=[txt], model=model, dimensions=size).data[0].embedding


weapons_tests = read_txt_files("assignments/data/pliki_z_fabryki/do-not-share")

weapons_tests_embeddings = []
for filename, test_text in weapons_tests.items():
    weapons_tests_embeddings.append({
        "id": str(uuid.uuid4()),
        "vector": get_embedding(test_text, 1024),
        "payload": {
            "text": test_text,
            "filename": filename
        }
    })


# Insert points into the collection
qdrant_client.upsert(
    collection_name=collection_name,
    points=[
        PointStruct(
            id=test['id'],
            vector=test['vector'],
            payload=test['payload']
        )
        for test in weapons_tests_embeddings
    ]
)

# Search for similar vectors
search_for_text = "W raporcie, z którego dnia znajduje się wzmianka o kradzieży prototypu broni?"
hit = qdrant_client.search(
    collection_name=collection_name,
    query_vector=get_embedding(search_for_text, 1024),
    limit=1
)

result = hit[0].payload["filename"].replace(".txt", "").replace("_", "-")
print('results: ', result)

payload = {
    "task": "wektory",
    "apikey": AIDEVS_MY_APIKEY,
    "answer": result
}
print(f"payload: {payload}")
post_json_data_to_url(payload, f"{CENTRALA_BASE_URL}/report")
