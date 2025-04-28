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
from ..content_management.service import ContentManagementService


class NewsManagementMCP:
    """
    Model Context Protocol server for news management.
    Implements tools for collecting and displaying news.
    """

    def __init__(self, interests_file: str = None, reset_db: bool = False):
        """
        Initialize the MCP server for news management.

        Args:
            interests_file: Path to file containing user interests
            reset_db: Whether to reset the vector database
        """
        self.tavily = TavilyNewsWrapper()
        self.interests_file = interests_file or os.path.join(
            "data", "user_interests", "sample_interests.txt"
        )

        # Initialize content management service
        self.content_service = ContentManagementService(reset_db=reset_db)

        # Initialize MCP server and tools
        self.app = FastAPI()
        self.mcp_server = MCPServer(app=self.app)

        # Register tools
        self._register_tools()

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

        # Summarize story tool
        summarize_story_tool = Tool(
            name="summarize-story",
            description="Get a detailed summary of a specific news story",
            function=self.summarize_story,
            parameters={
                "type": "object",
                "properties": {
                    "story_id": {
                        "type": "string",
                        "description": "ID of the story to summarize",
                    }
                },
                "required": ["story_id"],
            },
        )

        # Answer question tool
        answer_question_tool = Tool(
            name="answer-question",
            description="Answer a question about news stories",
            function=self.answer_question,
            parameters={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "Question to answer",
                    },
                    "story_id": {
                        "type": "string",
                        "description": "ID of a specific story to answer from (optional)",
                        "default": "",
                    },
                },
                "required": ["question"],
            },
        )

        # Register all tools with the MCP server
        self.mcp_server.add_tool(collect_news_tool)
        self.mcp_server.add_tool(display_news_stories_tool)
        self.mcp_server.add_tool(display_interesting_stories_tool)
        self.mcp_server.add_tool(summarize_story_tool)
        self.mcp_server.add_tool(answer_question_tool)

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

        # Combine all collected news
        all_news = top_news + interest_news

        # Process the news using content management service
        result = self.content_service.process_news(all_news)

        # Return collection summary
        return {
            "status": "success",
            "total_collected": len(all_news),
            "top_news_count": len(top_news),
            "interest_news_count": len(interest_news),
            "interests": interests,
            "categories": result.get("categories", {}),
            "raw_stored": result.get("raw_count", 0),
            "normalized_stored": result.get("normalized_count", 0),
        }

    def display_news_stories(self, category: str = "all") -> Dict[str, Any]:
        """
        Display a list of normalized headlines related to major stories.

        Args:
            category: Category of news to display

        Returns:
            Dictionary with news stories
        """
        # Get news from the content management service
        news_stories = self.content_service.get_news_by_category(
            category if category != "all" else None
        )

        if not news_stories:
            return {
                "status": "error",
                "message": f"No news found for category: {category}. Run collect-news first.",
            }

        result = {"status": "success", "stories": []}

        # Format stories
        for story in news_stories:
            result["stories"].append(
                {
                    "id": story.get("id", ""),
                    "title": story.get("title", ""),
                    "url": story.get("url", ""),
                    "published_date": story.get("published_date", ""),
                    "category": story.get("category", ""),
                    "summary": story.get("summary", ""),
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
        # Get news from the content management service
        news_stories = self.content_service.get_news_by_interest(
            interest if interest else None
        )

        if not news_stories:
            return {
                "status": "error",
                "message": f"No news found for interest: {interest if interest else 'any'}. Run collect-news first.",
            }

        result = {"status": "success", "stories": []}

        # Format stories
        for story in news_stories:
            result["stories"].append(
                {
                    "id": story.get("id", ""),
                    "title": story.get("title", ""),
                    "url": story.get("url", ""),
                    "published_date": story.get("published_date", ""),
                    "category": story.get("category", ""),
                    "interest": story.get("interest", ""),
                    "summary": story.get("summary", ""),
                }
            )

        result["count"] = len(result["stories"])
        return result

    def summarize_story(self, story_id: str) -> Dict[str, Any]:
        """
        Get a detailed summary of a specific news story.

        Args:
            story_id: ID of the story to summarize

        Returns:
            Dictionary with story summary
        """
        return self.content_service.summarize_story(story_id)

    def answer_question(self, question: str, story_id: str = "") -> Dict[str, Any]:
        """
        Answer a question about news stories.

        Args:
            question: Question to answer
            story_id: ID of a specific story to answer from (optional)

        Returns:
            Dictionary with answer
        """
        return self.content_service.answer_question(
            question, story_id if story_id else None
        )

    def start(self, host: str = "0.0.0.0", port: int = 8000):
        """
        Start the MCP server.

        Args:
            host: Host to listen on
            port: Port to listen on
        """
        import uvicorn

        uvicorn.run(self.app, host=host, port=port)


def create_mcp_server(
    interests_file: Optional[str] = None, reset_db: bool = False
) -> NewsManagementMCP:
    """
    Create and return a NewsManagementMCP instance.

    Args:
        interests_file: Path to file containing user interests
        reset_db: Whether to reset the vector database

    Returns:
        NewsManagementMCP instance
    """
    return NewsManagementMCP(interests_file=interests_file, reset_db=reset_db)


# For testing purposes
if __name__ == "__main__":
    import dotenv

    dotenv.load_dotenv()

    # Create and start the MCP server
    mcp = create_mcp_server()

    print("Starting News Management MCP server on http://localhost:8000")
    mcp.start()
