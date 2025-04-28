"""
News Categorization Service

This module provides functionality for categorizing news stories into different categories.
It uses LLMs to determine appropriate categories for news articles.
"""

import os
from typing import List, Dict, Any, Union
import asyncio
from concurrent.futures import ThreadPoolExecutor

from langchain_community.llms import Ollama
from pydantic import BaseModel, Field


class NewsCategory(BaseModel):
    """Model for news category classification"""

    category: str = Field(description="The primary category of the news article")
    confidence: float = Field(description="Confidence score (0-1)")
    subcategories: List[str] = Field(
        default_factory=list, description="List of subcategories"
    )


class NewsCategorizationService:
    """Service for categorizing news stories"""

    CATEGORIES = ["world", "us", "sports", "financial", "technology", "other"]

    def __init__(self, model_name: str = None, ollama_base_url: str = None):
        """
        Initialize the news categorization service.

        Args:
            model_name: Name of the LLM model to use
            ollama_base_url: Base URL for Ollama
        """
        self.model_name = model_name or os.getenv("MODEL_NAME", "llama3")
        self.ollama_base_url = ollama_base_url or os.getenv(
            "OLLAMA_BASE_URL", "http://localhost:11434"
        )

        # Initialize LLM
        self.llm = Ollama(model=self.model_name, base_url=self.ollama_base_url)

    def categorize_news_item(self, news_item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Categorize a single news item.

        Args:
            news_item: News item to categorize

        Returns:
            News item with category added
        """
        title = news_item.get("title", "")
        content = news_item.get("content", "")

        # If both title and content are empty, return as 'other'
        if not title and not content:
            news_item["category"] = "other"
            return news_item

        # Create a prompt for the LLM
        prompt = f"""
Categorize the following news article into exactly ONE of these categories:
- world: For international news, global events, and news about countries other than the US
- us: For US domestic news, politics, and events within the United States
- sports: For sports-related news, games, athletes, and sporting events
- financial: For news about markets, economy, business, and finance
- technology: For news about technology, software, hardware, AI, and digital developments
- other: For news that doesn't fit clearly into any of the above categories

News Title: {title}

News Content (excerpt): {content[:500]}...

Respond with the single most appropriate category name only (lowercase). For example, just respond with "world" or "technology".
"""

        # Get category from LLM
        try:
            category = self.llm.invoke(prompt).strip().lower()

            # Validate that the category is in our list
            if category not in self.CATEGORIES:
                # Default to 'other' if invalid
                category = "other"

            # Add category to news item
            news_item["category"] = category

        except Exception as e:
            print(f"Error categorizing news item: {e}")
            # Default to 'other' in case of error
            news_item["category"] = "other"

        return news_item

    def categorize_news(
        self, news_items: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Categorize a list of news items and organize them by category.

        Args:
            news_items: List of news items to categorize

        Returns:
            Dictionary with categories as keys and lists of news items as values
        """
        # Initialize result dictionary
        categorized = {category: [] for category in self.CATEGORIES}

        # Categorize each news item
        for item in news_items:
            categorized_item = self.categorize_news_item(item)
            category = categorized_item.get("category", "other")
            categorized[category].append(categorized_item)

        return categorized

    async def categorize_news_async(
        self, news_items: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Categorize a list of news items asynchronously.

        Args:
            news_items: List of news items to categorize

        Returns:
            Dictionary with categories as keys and lists of news items as values
        """
        # Initialize result dictionary
        categorized = {category: [] for category in self.CATEGORIES}

        # Define coroutine to categorize in thread pool
        async def categorize_in_thread(item):
            with ThreadPoolExecutor() as executor:
                return await asyncio.get_event_loop().run_in_executor(
                    executor, self.categorize_news_item, item
                )

        # Create tasks for each news item
        tasks = [categorize_in_thread(item) for item in news_items]
        categorized_items = await asyncio.gather(*tasks)

        # Organize by category
        for item in categorized_items:
            category = item.get("category", "other")
            categorized[category].append(item)

        return categorized

    def simple_categorize_news(
        self, news_items: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Categorize news items using simple keyword matching (fallback method).

        Args:
            news_items: List of news items to categorize

        Returns:
            Dictionary with categories as keys and lists of news items as values
        """
        categorized = {category: [] for category in self.CATEGORIES}

        for item in news_items:
            title = item.get("title", "").lower()
            content_start = item.get("content", "")[:100].lower()

            # Simple keyword-based categorization
            if any(
                word in title or word in content_start
                for word in [
                    "world",
                    "global",
                    "international",
                    "europe",
                    "asia",
                    "africa",
                ]
            ):
                category = "world"
            elif any(
                word in title or word in content_start
                for word in ["us", "united states", "america", "washington"]
            ):
                category = "us"
            elif any(
                word in title or word in content_start
                for word in [
                    "sport",
                    "game",
                    "team",
                    "player",
                    "match",
                    "ball",
                    "tournament",
                ]
            ):
                category = "sports"
            elif any(
                word in title or word in content_start
                for word in [
                    "market",
                    "stock",
                    "economy",
                    "business",
                    "finance",
                    "dollar",
                    "bank",
                ]
            ):
                category = "financial"
            elif any(
                word in title or word in content_start
                for word in [
                    "tech",
                    "technology",
                    "software",
                    "computer",
                    "digital",
                    "ai",
                    "app",
                ]
            ):
                category = "technology"
            else:
                category = "other"

            # Add category to news item
            item["category"] = category
            categorized[category].append(item)

        return categorized


# For testing purposes
if __name__ == "__main__":
    categorizer = NewsCategorizationService()

    # Test categorization
    test_item = {
        "title": "Global Markets See Sharp Decline Amid Inflation Fears",
        "content": "Global markets experienced significant downturns today as new inflation data sparked concerns about central bank policies. Analysts suggest this could impact economic growth in both developed and emerging markets.",
    }

    categorized = categorizer.categorize_news_item(test_item)
    print(f"Categorized as: {categorized['category']}")

    # Test multiple items
    test_items = [
        {
            "title": "New AI Tool Revolutionizes Software Development",
            "content": "A new artificial intelligence tool claims to increase programmer productivity by 200%. The system can generate code based on natural language descriptions.",
        },
        {
            "title": "US Senate Passes Infrastructure Bill",
            "content": "The United States Senate passed a long-awaited infrastructure bill today, allocating billions toward roads, bridges, and broadband internet.",
        },
    ]

    categorized = categorizer.categorize_news(test_items)
    for category, items in categorized.items():
        if items:
            print(f"\nCategory: {category}")
            for item in items:
                print(f"- {item['title']}")
