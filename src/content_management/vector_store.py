"""
Vector Store for News Content

This module provides a vector store implementation using Chroma for storing news content.
It handles storage, retrieval, and querying of news stories.
"""

import os
from typing import List, Dict, Any, Optional
import uuid
import json
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions


class VectorStore:
    """Vector store for news content using Chroma"""

    def __init__(self, persist_directory: Optional[str] = None):
        """
        Initialize the vector store.

        Args:
            persist_directory: Directory to persist the vector store (optional)
        """
        self.persist_directory = persist_directory or os.path.join("data", "chroma_db")

        # Ensure the directory exists
        os.makedirs(self.persist_directory, exist_ok=True)

        # Initialize Chroma client
        self.client = chromadb.PersistentClient(path=self.persist_directory)

        # Use default embedding function (all-MiniLM-L6-v2)
        self.embedding_function = embedding_functions.DefaultEmbeddingFunction()

        # Initialize collections
        self.raw_collection = self.client.get_or_create_collection(
            name="raw_news", embedding_function=self.embedding_function
        )

        self.normalized_collection = self.client.get_or_create_collection(
            name="normalized_news", embedding_function=self.embedding_function
        )

    def reset_collections(self):
        """Reset both collections by deleting and recreating them"""
        # Delete existing collections if they exist
        try:
            self.client.delete_collection("raw_news")
            self.client.delete_collection("normalized_news")
        except Exception as e:
            print(f"Error while deleting collections: {e}")

        # Recreate collections
        self.raw_collection = self.client.get_or_create_collection(
            name="raw_news", embedding_function=self.embedding_function
        )

        self.normalized_collection = self.client.get_or_create_collection(
            name="normalized_news", embedding_function=self.embedding_function
        )

        return {"status": "success", "message": "Collections reset successfully"}

    def add_raw_news(self, news_items: List[Dict[str, Any]]):
        """
        Add raw news items to the vector store.

        Args:
            news_items: List of news items to add
        """
        documents = []
        metadatas = []
        ids = []

        for item in news_items:
            # Extract text content for embedding
            content = item.get("content", "")
            title = item.get("title", "")

            # Skip if no content
            if not content and not title:
                continue

            # Generate document text (combining title and content)
            document = f"{title}\n\n{content}"
            documents.append(document)

            # Create metadata
            metadata = {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "published_date": item.get("published_date", ""),
                "source": item.get("source", ""),
                "interest": item.get("interest", ""),
                "category": item.get("category", "other"),
            }
            metadatas.append(metadata)

            # Generate a unique ID
            doc_id = str(uuid.uuid4())
            ids.append(doc_id)

        # Add to collection
        if documents:
            self.raw_collection.add(documents=documents, metadatas=metadatas, ids=ids)

        return len(documents)

    def add_normalized_news(self, news_items: List[Dict[str, Any]]):
        """
        Add normalized news items to the vector store.

        Args:
            news_items: List of normalized news items to add
        """
        documents = []
        metadatas = []
        ids = []

        for item in news_items:
            # Extract text content for embedding
            summary = item.get("summary", "")
            title = item.get("title", "")

            # Skip if no summary
            if not summary and not title:
                continue

            # Generate document text
            document = f"{title}\n\n{summary}"
            documents.append(document)

            # Create metadata
            metadata = {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "published_date": item.get("published_date", ""),
                "source": item.get("source", ""),
                "interest": item.get("interest", ""),
                "category": item.get("category", "other"),
                # Convert list to string for Chroma compatibility
                "related_stories": json.dumps(item.get("related_stories", [])),
            }
            metadatas.append(metadata)

            # Generate a unique ID or use provided one
            doc_id = item.get("id", str(uuid.uuid4()))
            ids.append(doc_id)

        # Add to collection
        if documents:
            self.normalized_collection.add(
                documents=documents, metadatas=metadatas, ids=ids
            )

        return len(documents)

    def get_raw_news_by_category(self, category: str = None) -> List[Dict[str, Any]]:
        """
        Get raw news items by category.

        Args:
            category: Category to filter by (optional)

        Returns:
            List of news items
        """
        if category and category.lower() != "all":
            results = self.raw_collection.get(where={"category": category.lower()})
        else:
            results = self.raw_collection.get()

        # Convert to list of dictionaries
        items = []
        for i in range(len(results["ids"])):
            item = {"id": results["ids"][i], "document": results["documents"][i]}

            # Add metadata
            if "metadatas" in results and results["metadatas"]:
                item.update(results["metadatas"][i])

            items.append(item)

        return items

    def get_normalized_news_by_category(
        self, category: str = None
    ) -> List[Dict[str, Any]]:
        """
        Get normalized news items by category.

        Args:
            category: Category to filter by (optional)

        Returns:
            List of news items
        """
        if category and category.lower() != "all":
            results = self.normalized_collection.get(
                where={"category": category.lower()}
            )
        else:
            results = self.normalized_collection.get()

        # Convert to list of dictionaries
        items = []
        for i in range(len(results["ids"])):
            item = {"id": results["ids"][i], "document": results["documents"][i]}

            # Add metadata
            if "metadatas" in results and results["metadatas"]:
                item.update(results["metadatas"][i])

            items.append(item)

        return items

    def get_news_by_interest(self, interest: str = None) -> List[Dict[str, Any]]:
        """
        Get news items by interest.

        Args:
            interest: Interest to filter by (optional)

        Returns:
            List of news items
        """
        if interest:
            results = self.normalized_collection.get(
                where={"interest": interest.lower()}
            )
        else:
            # Get all items with non-empty interest
            results = self.normalized_collection.get()

        # Convert to list of dictionaries and filter
        items = []
        for i in range(len(results["ids"])):
            metadata = results["metadatas"][i] if "metadatas" in results else {}

            if not interest or "interest" in metadata and metadata["interest"]:
                item = {"id": results["ids"][i], "document": results["documents"][i]}

                # Add metadata
                if metadata:
                    item.update(metadata)

                items.append(item)

        return items

    def query_news(
        self, query: str, collection: str = "normalized", n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Query news items.

        Args:
            query: Query string
            collection: Which collection to query ("normalized" or "raw")
            n_results: Number of results to return

        Returns:
            List of news items
        """
        if collection == "raw":
            collection_obj = self.raw_collection
        else:
            collection_obj = self.normalized_collection

        results = collection_obj.query(query_texts=[query], n_results=n_results)

        # Convert to list of dictionaries
        items = []
        if results["distances"] and results["documents"]:
            for i in range(len(results["documents"][0])):
                item = {
                    "id": results["ids"][0][i],
                    "document": results["documents"][0][i],
                    "distance": results["distances"][0][i],
                }

                # Add metadata
                if "metadatas" in results and results["metadatas"][0]:
                    item.update(results["metadatas"][0][i])

                items.append(item)

        return items


# For testing purposes
if __name__ == "__main__":
    store = VectorStore()
    print("Vector store initialized successfully!")

    # Test adding some news items
    news_items = [
        {
            "title": "Test News Item 1",
            "content": "This is a test news item about technology.",
            "url": "https://example.com/1",
            "published_date": "2023-01-01",
            "source": "test",
            "category": "technology",
        },
        {
            "title": "Test News Item 2",
            "content": "This is a test news item about sports.",
            "url": "https://example.com/2",
            "published_date": "2023-01-01",
            "source": "test",
            "category": "sports",
        },
    ]

    count = store.add_raw_news(news_items)
    print(f"Added {count} news items to raw collection")

    # Test querying
    results = store.query_news("technology", collection="raw")
    print(f"Found {len(results)} results for 'technology'")
    for result in results:
        print(f"- {result['title']} (Distance: {result['distance']})")
