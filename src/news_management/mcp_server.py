"""
MCP Server for News Management

This module implements a Model Context Protocol server for news management.
It wraps the Tavily functionality and provides tools for news collection,
displaying news stories, and displaying stories based on user interests.
"""

import os
import json
from typing import List, Dict, Any, Optional
from pathlib import Path

from mcp import MCPServer
from mcp.tools import Tool
from fastapi import FastAPI

from .tavily_wrapper import TavilyNewsWrapper

# Import from content_management when it's created
# from ..content_management.vector_store import VectorStore
# from ..content_management.categorizer import NewsCategorizationService
# from ..content_management.normalizer import NewsNormalizer


class NewsManagementMCP:
    """
    Model Context Protocol server for news management.
    Implements tools for collecting and displaying news.
    """

    def __init__(
        self,
        interests_file: str = None,
        vector_store=None,
        categorizer=None,
        normalizer=None,
    ):
        """
        Initialize the MCP server for news management.

        Args:
            interests_file: Path to file containing user interests
            vector_store: Vector store for storing news stories
            categorizer: News categorization service
            normalizer: News normalizer service
        """
        self.tavily = TavilyNewsWrapper()
        self.interests_file = interests_file or os.path.join(
            "data", "user_interests", "sample_interests.txt"
        )

        # Store the content management services
        # These will be implemented later
        self.vector_store = vector_store
        self.categorizer = categorizer
        self.normalizer = normalizer

        # Initialize MCP server and tools
        self.app = FastAPI()
        self.mcp_server = MCPServer(app=self.app)

        # Register tools
        self._register_tools()

        # Store for collected news (temporary solution until vector store is implemented)
        self.collected_news = []
        self.categorized_news = {}
        self.interesting_news = []

    def _register_tools(self):
        """Register MCP tools"""

        # Collect news tool
        collect_news_tool = Tool(
            name="collect-news",
            description="Collect major news stories from the last day and stories matching user interests",
            function=self.collect_news,
            parameters={
                "type": "object",
                "properties": {
                    "max_top_results": {
                        "type": "integer",
                        "description": "Maximum number of top news results to collect",
                        "default": 10,
                    },
                    "max_interest_results": {
                        "type": "integer",
                        "description": "Maximum number of results per interest",
                        "default": 3,
                    },
                },
            },
        )

        # Display news stories tool
        display_news_stories_tool = Tool(
            name="display-news-stories",
            description="Display a list of normalized headlines related to major stories and user's interests",
            function=self.display_news_stories,
            parameters={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Category of news to display (world, us, sports, financial, technology, other)",
                        "enum": [
                            "all",
                            "world",
                            "us",
                            "sports",
                            "financial",
                            "technology",
                            "other",
                        ],
                        "default": "all",
                    }
                },
            },
        )

        # Display interesting stories tool
        display_interesting_stories_tool = Tool(
            name="display-interesting-stories",
            description="Display only the stories that align with user's interests",
            function=self.display_interesting_stories,
            parameters={
                "type": "object",
                "properties": {
                    "interest": {
                        "type": "string",
                        "description": "Specific interest to filter by (optional)",
                        "default": "",
                    }
                },
            },
        )

        # Register all tools with the MCP server
        self.mcp_server.add_tool(collect_news_tool)
        self.mcp_server.add_tool(display_news_stories_tool)
        self.mcp_server.add_tool(display_interesting_stories_tool)

    def collect_news(
        self, max_top_results: int = 10, max_interest_results: int = 3
    ) -> Dict[str, Any]:
        """
        Collect news stories and store them in the vector database.

        Args:
            max_top_results: Maximum number of top news results to collect
            max_interest_results: Maximum number of results per interest

        Returns:
            Dictionary with collection summary
        """
        # First, read user interests
        interests = self.tavily.read_interests_from_file(self.interests_file)

        # Collect top news
        top_news = self.tavily.collect_top_news(max_top_results)

        # Collect news by interests
        interest_news = self.tavily.collect_news_by_interests(
            interests, max_interest_results
        )

        # Store all collected news
        all_news = top_news + interest_news
        self.collected_news = all_news

        # When content management is implemented, we would:
        # 1. Store raw news in vector store
        # if self.vector_store:
        #     self.vector_store.add_documents(all_news)

        # 2. Categorize news
        # if self.categorizer:
        #     self.categorized_news = self.categorizer.categorize_news(all_news)
        # else:
        # Temporary solution: simple categorization
        self._simple_categorize_news(all_news)

        # 3. Normalize news
        # if self.normalizer:
        #     normalized_news = self.normalizer.normalize_news(all_news)
        #     self.vector_store.add_normalized_news(normalized_news)

        # 4. Mark interest-related news
        self.interesting_news = interest_news

        # Return collection summary
        return {
            "status": "success",
            "total_collected": len(all_news),
            "top_news_count": len(top_news),
            "interest_news_count": len(interest_news),
            "interests": interests,
            "categories": list(self.categorized_news.keys()),
        }

    def _simple_categorize_news(self, news_stories: List[Dict[str, Any]]):
        """
        Simple categorization based on title keywords.
        This is a temporary solution until the real categorizer is implemented.

        Args:
            news_stories: List of news stories to categorize
        """
        categories = {
            "world": [],
            "us": [],
            "sports": [],
            "financial": [],
            "technology": [],
            "other": [],
        }

        for story in news_stories:
            title = story["title"].lower()

            # Very simple keyword-based categorization
            if any(
                word in title
                for word in [
                    "world",
                    "global",
                    "international",
                    "europe",
                    "asia",
                    "africa",
                ]
            ):
                categories["world"].append(story)
            elif any(
                word in title
                for word in ["us", "united states", "america", "washington"]
            ):
                categories["us"].append(story)
            elif any(
                word in title
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
                categories["sports"].append(story)
            elif any(
                word in title
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
                categories["financial"].append(story)
            elif any(
                word in title
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
                categories["technology"].append(story)
            else:
                categories["other"].append(story)

        self.categorized_news = categories

    def display_news_stories(self, category: str = "all") -> Dict[str, Any]:
        """
        Display a list of normalized headlines related to major stories.

        Args:
            category: Category of news to display

        Returns:
            Dictionary with news stories
        """
        if not self.collected_news:
            return {
                "status": "error",
                "message": "No news collected yet. Run collect-news first.",
            }

        result = {"status": "success", "stories": []}

        if category == "all":
            # Return all stories
            for story in self.collected_news:
                result["stories"].append(
                    {
                        "title": story["title"],
                        "url": story["url"],
                        "published_date": story["published_date"],
                    }
                )
        else:
            # Return stories from a specific category
            if category in self.categorized_news:
                for story in self.categorized_news[category]:
                    result["stories"].append(
                        {
                            "title": story["title"],
                            "url": story["url"],
                            "published_date": story["published_date"],
                        }
                    )

        result["count"] = len(result["stories"])
        return result

    def display_interesting_stories(self, interest: str = "") -> Dict[str, Any]:
        """
        Display only the stories that align with user's interests.

        Args:
            interest: Specific interest to filter by (optional)

        Returns:
            Dictionary with interesting news stories
        """
        if not self.interesting_news:
            return {
                "status": "error",
                "message": "No interest-based news collected yet. Run collect-news first.",
            }

        result = {"status": "success", "stories": []}

        if interest:
            # Filter by specific interest
            for story in self.interesting_news:
                if story.get("interest", "").lower() == interest.lower():
                    result["stories"].append(
                        {
                            "title": story["title"],
                            "url": story["url"],
                            "published_date": story["published_date"],
                            "interest": story.get("interest", ""),
                        }
                    )
        else:
            # Return all interesting stories
            for story in self.interesting_news:
                result["stories"].append(
                    {
                        "title": story["title"],
                        "url": story["url"],
                        "published_date": story["published_date"],
                        "interest": story.get("interest", ""),
                    }
                )

        result["count"] = len(result["stories"])
        return result

    def start(self, host: str = "0.0.0.0", port: int = 8000):
        """
        Start the MCP server.

        Args:
            host: Host to listen on
            port: Port to listen on
        """
        import uvicorn

        uvicorn.run(self.app, host=host, port=port)


def create_mcp_server(interests_file: Optional[str] = None) -> NewsManagementMCP:
    """
    Create and return a NewsManagementMCP instance.

    Args:
        interests_file: Path to file containing user interests

    Returns:
        NewsManagementMCP instance
    """
    return NewsManagementMCP(interests_file=interests_file)


# For testing purposes
if __name__ == "__main__":
    import dotenv

    dotenv.load_dotenv()

    # Create and start the MCP server
    mcp = create_mcp_server()

    print("Starting News Management MCP server on http://localhost:8000")
    mcp.start()
