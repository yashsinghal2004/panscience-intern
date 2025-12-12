"""Example script to test the RAG API."""

import requests
import json

API_URL = "http://localhost:8000/api/v1"


def test_health():
    """Test health endpoint."""
    print("Testing health endpoint...")
    response = requests.get(f"{API_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()


def test_ingest_text():
    """Test text ingestion."""
    print("Testing text ingestion...")
    sample_text = """
    Artificial Intelligence (AI) is transforming the way we work and live.
    Machine learning, a subset of AI, enables computers to learn from data
    without being explicitly programmed. Deep learning uses neural networks
    with multiple layers to process complex patterns in data.
    """
    
    response = requests.post(
        f"{API_URL}/ingest",
        json={"text": sample_text}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()


def test_query():
    """Test query endpoint."""
    print("Testing query endpoint...")
    response = requests.post(
        f"{API_URL}/query",
        json={"query": "What is artificial intelligence?"}
    )
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Answer: {result.get('answer', 'N/A')}")
    print(f"Sources: {len(result.get('sources', []))}")
    print()


if __name__ == "__main__":
    print("=" * 50)
    print("RAG API Test Script")
    print("=" * 50)
    print()
    
    try:
        test_health()
        test_ingest_text()
        test_query()
        print("All tests completed!")
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to API. Make sure the server is running.")
    except Exception as e:
        print(f"Error: {e}")











