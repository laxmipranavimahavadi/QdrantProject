from flask import Flask, request, jsonify
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance
from langchain.document_loaders import PyPDFLoader
import os
import uuid

app = Flask(__name__)

# Predefined folder containing PDFs
manuals_folder = "product_manuals"  # Ensure this folder exists and contains your PDFs

if not os.path.exists(manuals_folder):
    os.makedirs(manuals_folder)
    print(f"Created folder: {manuals_folder}")

# Connect to Qdrant
qdrant_client = QdrantClient(url="http://localhost:6333")
qdrant_index_name = "product_manuals"

# Initialize SentenceTransformer model for embeddings
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# Check if the collection exists, and create if not
if not qdrant_client.collection_exists(collection_name=qdrant_index_name):
    qdrant_client.create_collection(
        collection_name=qdrant_index_name,
        vectors_config=VectorParams(
            size=embedding_model.get_sentence_embedding_dimension(),  # Vector size
            distance=Distance.COSINE  # Distance metric
        )
    )

# Function to process PDFs and index in Qdrant
def process_pdfs_and_index(folder_path):
    try:
        for filename in os.listdir(folder_path):
            if filename.endswith(".pdf"):
                file_path = os.path.join(folder_path, filename)
                loader = PyPDFLoader(file_path)
                documents = loader.load()

                for doc in documents:
                    embedding = embedding_model.encode([doc.page_content])[0]
                    doc_id = uuid.uuid4()  # Use UUID for document ID
                    qdrant_client.upsert(
                        collection_name=qdrant_index_name,
                        points=[{
                            "id": str(doc_id),
                            "vector": embedding,
                            "payload": {"text": doc.page_content, "source": filename}
                        }]
                    )
        print("PDFs processed and indexed successfully.")
    except Exception as e:
        print(f"Error processing PDFs: {e}")

# Call the processing function at app startup
process_pdfs_and_index(manuals_folder)

# API route to query Qdrant
@app.route("/query", methods=["POST"])
def search():
    try:
        query = request.json.get("query")
        if not query:
            return jsonify({"error": "Query is required"}), 400

        # Generate query embedding
        query_embedding = embedding_model.encode([query])[0]  # Generate embedding for the query

        # Perform similarity search in Qdrant
        results = qdrant_client.search(
            collection_name=qdrant_index_name,
            query_vector=query_embedding,
            limit=5  # Return top 5 most relevant documents
        )

        # Format response
        response = [
            {
                "content": r.payload["text"],
                "source": r.payload.get("source", "Unknown"),
                "score": r.score
            } for r in results
        ]
        return jsonify(response), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
