"""
Tavily Wrapper for News Collection

This module provides a wrapper around the Tavily API for news collection.
It handles fetching news stories based on general topics and user interests.
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from tavily import TavilyClient


class TavilyNewsWrapper:
    """Wrapper for the Tavily API for news collection"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Tavily wrapper.

        Args:
            api_key: Tavily API key (optional, will use environment variable if not provided)
        """
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Tavily API key not provided and not found in environment variables"
            )

        self.client = TavilyClient(api_key=self.api_key)

    def collect_top_news(self, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Collect top news stories from the last day.

        Args:
            max_results: Maximum number of results to return

        Returns:
            List of news stories with title, content, url, and published_date
        """
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        date_str = yesterday.strftime("%Y-%m-%d")

        query = f"top news stories since {date_str}"

        search_result = self.client.search(
            query=query,
            search_depth="advanced",
            include_answer=False,
            include_images=False,
            include_raw_content=True,
            max_results=max_results,
        )

        # Process and normalize the results
        stories = []
        for result in search_result.get("results", []):
            stories.append(
                {
                    "title": result.get("title", ""),
                    "content": result.get("content", ""),
                    "url": result.get("url", ""),
                    "published_date": result.get("published_date", ""),
                    "source": "tavily_top_news",
                    "raw_data": result,
                }
            )

        return stories

    def collect_news_by_interest(
        self, interest: str, max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Collect news stories related to a specific interest from the last day.

        Args:
            interest: Topic of interest
            max_results: Maximum number of results to return

        Returns:
            List of news stories with title, content, url, and published_date
        """
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        date_str = yesterday.strftime("%Y-%m-%d")

        query = f"latest news about {interest} since {date_str}"

        search_result = self.client.search(
            query=query,
            search_depth="advanced",
            include_answer=False,
            include_images=False,
            include_raw_content=True,
            max_results=max_results,
        )

        # Process and normalize the results
        stories = []
        for result in search_result.get("results", []):
            stories.append(
                {
                    "title": result.get("title", ""),
                    "content": result.get("content", ""),
                    "url": result.get("url", ""),
                    "published_date": result.get("published_date", ""),
                    "source": f"tavily_interest_{interest}",
                    "interest": interest,
                    "raw_data": result,
                }
            )

        return stories

    def collect_news_by_interests(
        self, interests: List[str], max_results_per_interest: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Collect news stories related to multiple interests from the last day.

        Args:
            interests: List of topics of interest
            max_results_per_interest: Maximum number of results to return per interest

        Returns:
            List of news stories with title, content, url, and published_date
        """
        all_stories = []

        for interest in interests:
            stories = self.collect_news_by_interest(interest, max_results_per_interest)
            all_stories.extend(stories)

        return all_stories

    def read_interests_from_file(self, file_path: str) -> List[str]:
        """
        Read interests from a file.

        Args:
            file_path: Path to the file containing interests (one per line)

        Returns:
            List of interests
        """
        interests = []
        try:
            with open(file_path, "r") as f:
                for line in f:
                    interest = line.strip()
                    if interest:
                        interests.append(interest)
        except Exception as e:
            print(f"Error reading interests file: {e}")

        return interests


# For testing
if __name__ == "__main__":
    import dotenv

    dotenv.load_dotenv()

    wrapper = TavilyNewsWrapper()

    # Test getting top news
    top_news = wrapper.collect_top_news(3)
    print(f"Found {len(top_news)} top news stories")
    for i, story in enumerate(top_news):
        print(f"{i+1}. {story['title']} - {story['url']}")

    # Test getting news by interest
    interest_news = wrapper.collect_news_by_interest("artificial intelligence", 2)
    print(f"\nFound {len(interest_news)} AI news stories")
    for i, story in enumerate(interest_news):
        print(f"{i+1}. {story['title']} - {story['url']}")
