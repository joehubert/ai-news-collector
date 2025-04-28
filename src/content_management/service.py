"""
Content Management Service

This module provides a unified service for content management operations:
- Categorizing news stories
- Normalizing/summarizing news stories
- Storing news content in a vector database
- Retrieving news content
"""

import os
import json
from typing import List, Dict, Any, Optional

from .vector_store import VectorStore
from .categorizer import NewsCategorizationService
from .normalizer import NewsNormalizer


class ContentManagementService:
    """Unified service for content management operations"""

    def __init__(
        self,
        model_name: str = None,
        ollama_base_url: str = None,
        vector_store_path: str = None,
        reset_db: bool = False,
    ):
        """
        Initialize the content management service.

        Args:
            model_name: Name of the LLM model to use
            ollama_base_url: Base URL for Ollama
            vector_store_path: Path to the vector store
            reset_db: Whether to reset the vector database
        """
        self.model_name = model_name or os.getenv("MODEL_NAME", "llama3")
        self.ollama_base_url = ollama_base_url or os.getenv(
            "OLLAMA_BASE_URL", "http://localhost:11434"
        )

        # Initialize components
        self.vector_store = VectorStore(persist_directory=vector_store_path)
        self.categorizer = NewsCategorizationService(
            model_name=self.model_name, ollama_base_url=self.ollama_base_url
        )
        self.normalizer = NewsNormalizer(
            model_name=self.model_name, ollama_base_url=self.ollama_base_url
        )

        # Reset vector database if requested
        if reset_db:
            self.vector_store.reset_collections()

    def process_news(self, news_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process news items through the full pipeline:
        1. Categorize news
        2. Store raw news
        3. Normalize news
        4. Group similar stories
        5. Store normalized news

        Args:
            news_items: List of news items to process

        Returns:
            Summary of processing results
        """
        if not news_items:
            return {
                "status": "error",
                "message": "No news items provided",
                "raw_count": 0,
                "normalized_count": 0,
            }

        print(f"Processing {len(news_items)} news items...")

        # Step 1: Categorize news
        print("Categorizing news...")
        try:
            categorized_news = self.categorizer.categorize_news(news_items)

            # Flatten the categorized news back to a list
            categorized_items = []
            for category, items in categorized_news.items():
                categorized_items.extend(items)

        except Exception as e:
            print(f"Error during categorization: {e}")
            print("Falling back to simple categorization...")
            categorized_news = self.categorizer.simple_categorize_news(news_items)

            # Flatten the categorized news back to a list
            categorized_items = []
            for category, items in categorized_news.items():
                categorized_items.extend(items)

        # Step 2: Store raw news
        print("Storing raw news...")
        raw_count = self.vector_store.add_raw_news(categorized_items)

        # Step 3: Normalize news
        print("Normalizing news...")
        normalized_items = self.normalizer.normalize_news(categorized_items)

        # Step 4: Group similar stories
        print("Grouping similar stories...")
        grouped_items = self.normalizer.group_similar_stories(normalized_items)

        # Step 5: Store normalized news
        print("Storing normalized news...")
        normalized_count = self.vector_store.add_normalized_news(grouped_items)

        # Return summary
        return {
            "status": "success",
            "raw_count": raw_count,
            "normalized_count": normalized_count,
            "categories": {
                category: len(items)
                for category, items in categorized_news.items()
                if items
            },
        }

    def get_news_by_category(self, category: str = None) -> List[Dict[str, Any]]:
        """
        Get news items by category.

        Args:
            category: Category to filter by (optional)

        Returns:
            List of news items
        """
        return self.vector_store.get_normalized_news_by_category(category)

    def get_news_by_interest(self, interest: str = None) -> List[Dict[str, Any]]:
        """
        Get news items by interest.

        Args:
            interest: Interest to filter by (optional)

        Returns:
            List of news items
        """
        return self.vector_store.get_news_by_interest(interest)

    def search_news(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search for news items.

        Args:
            query: Search query
            n_results: Number of results to return

        Returns:
            List of news items
        """
        return self.vector_store.query_news(query, n_results=n_results)

    def summarize_story(self, story_id: str) -> Dict[str, Any]:
        """
        Get a full summary for a specific story.

        Args:
            story_id: ID of the story to summarize

        Returns:
            Summary of the story
        """
        # Get the story from the normalized collection
        results = self.vector_store.normalized_collection.get(ids=[story_id])

        if not results or not results["ids"]:
            return {"status": "error", "message": "Story not found"}

        # Create summary result
        summary_result = {
            "status": "success",
            "id": story_id,
            "title": results["metadatas"][0].get("title", ""),
            "summary": results["documents"][0],
            "url": results["metadatas"][0].get("url", ""),
            "published_date": results["metadatas"][0].get("published_date", ""),
            "category": results["metadatas"][0].get("category", ""),
        }

        # Add related stories if available
        related_stories_str = results["metadatas"][0].get("related_stories", "[]")
        try:
            related_stories = json.loads(related_stories_str)
        except (json.JSONDecodeError, TypeError):
            related_stories = []

        if related_stories:
            related_results = self.vector_store.normalized_collection.get(
                ids=related_stories
            )

            summary_result["related_stories"] = [
                {
                    "id": related_results["ids"][i],
                    "title": related_results["metadatas"][i].get("title", ""),
                    "url": related_results["metadatas"][i].get("url", ""),
                }
                for i in range(len(related_results["ids"]))
            ]

        return summary_result

    def answer_question(
        self, question: str, story_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Answer a question about a news story or multiple stories.

        Args:
            question: Question to answer
            story_id: Specific story ID to answer from (optional)

        Returns:
            Answer to the question
        """
        # If story_id is provided, get that specific story
        if story_id:
            # Get the story from raw collection for more detail
            results = self.vector_store.raw_collection.get(ids=[story_id])

            if not results or not results["ids"]:
                return {"status": "error", "message": "Story not found"}

            content = results["documents"][0]
            title = results["metadatas"][0].get("title", "")

        else:
            # Find relevant stories based on the question
            relevant_stories = self.vector_store.query_news(
                query=question, collection="raw", n_results=3
            )

            if not relevant_stories:
                return {"status": "error", "message": "No relevant stories found"}

            # Compile content from relevant stories
            content = "\n\n".join(
                [
                    f"Article: {story['title']}\n{story['document']}"
                    for story in relevant_stories
                ]
            )

            title = "Multiple news articles"

        # Create a prompt for the LLM
        prompt = f"""
Based on the following news content, please answer this question:

Question: {question}

News Content:
{content}

Answer the question factually and concisely based only on the information provided in the news content. If the answer cannot be determined from the provided content, state that clearly.

Answer:
"""

        # Get answer from LLM
        try:
            answer = self.llm.invoke(prompt).strip()

            # Return result
            return {
                "status": "success",
                "question": question,
                "answer": answer,
                "source": title,
            }

        except Exception as e:
            print(f"Error generating answer: {e}")
            return {"status": "error", "message": f"Error generating answer: {e}"}

    @property
    def llm(self):
        """Get the LLM from the normalizer (for convenience)"""
        return self.normalizer.llm


# For testing purposes
if __name__ == "__main__":
    import dotenv

    dotenv.load_dotenv()

    # Initialize service
    service = ContentManagementService(reset_db=True)

    # Test with sample news items
    test_items = [
        {
            "title": "Global Markets See Sharp Decline Amid Inflation Fears",
            "content": "Global markets experienced significant downturns today as new inflation data sparked concerns about central bank policies. Major indices in Asia, Europe, and the US all fell by at least 2%. The S&P 500 dropped 2.3%, while the Nasdaq Composite fell 3.1%. Analysts suggest this could impact economic growth in both developed and emerging markets.",
            "url": "https://example.com/markets",
            "published_date": "2023-01-01",
        },
        {
            "title": "Tech Giant Announces New AI Chip",
            "content": "A leading technology company has unveiled a new AI chip that promises to deliver 50% better performance while using 30% less power. The chip will be available later this year.",
            "url": "https://example.com/tech",
            "published_date": "2023-01-01",
        },
        {
            "title": "US Senate Passes Infrastructure Bill",
            "content": "The United States Senate passed a long-awaited infrastructure bill today, allocating billions toward roads, bridges, and broadband internet.",
            "url": "https://example.com/politics",
            "published_date": "2023-01-01",
        },
    ]

    # Process news
    result = service.process_news(test_items)
    print("\nProcessing result:")
    print(f"Raw news items: {result['raw_count']}")
    print(f"Normalized news items: {result['normalized_count']}")
    print(f"Categories: {result['categories']}")

    # Test retrieval
    print("\nNews by category (financial):")
    financial_news = service.get_news_by_category("financial")
    for item in financial_news:
        print(f"- {item['title']}")

    # Test search
    print("\nSearch for 'infrastructure':")
    search_results = service.search_news("infrastructure")
    for item in search_results:
        print(f"- {item['title']} (Distance: {item['distance']})")
