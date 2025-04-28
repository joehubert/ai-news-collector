"""
News Normalizer Service

This module provides functionality for normalizing and summarizing news stories.
It also handles identification of similar/related news stories.
"""

import os
from typing import List, Dict, Any, Optional
import uuid
from collections import defaultdict

from langchain_community.llms import Ollama
from langchain_community.embeddings import OllamaEmbeddings
import numpy as np
from scipy.spatial.distance import cosine


class NewsNormalizer:
    """Service for normalizing news stories"""

    def __init__(self, model_name: str = None, ollama_base_url: str = None):
        """
        Initialize the news normalizer service.

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

        # Initialize embeddings for similarity detection
        try:
            self.embeddings = OllamaEmbeddings(
                model=self.model_name, base_url=self.ollama_base_url
            )
        except Exception as e:
            print(f"Warning: Could not initialize OllamaEmbeddings: {e}")
            self.embeddings = None

    def summarize_news_item(self, news_item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Summarize a single news item.

        Args:
            news_item: News item to summarize

        Returns:
            News item with summary added
        """
        title = news_item.get("title", "")
        content = news_item.get("content", "")

        # If both title and content are empty, return without summary
        if not title and not content:
            news_item["summary"] = ""
            return news_item

        # Create a prompt for the LLM
        prompt = f"""
Summarize the following news article in 3-4 sentences. Keep the summary concise but include all important details.

News Title: {title}

News Content: {content[:5000]}

Summary:
"""

        # Get summary from LLM
        try:
            summary = self.llm.invoke(prompt).strip()

            # Add summary to news item
            news_item["summary"] = summary

        except Exception as e:
            print(f"Error summarizing news item: {e}")
            # Default to title as summary in case of error
            news_item["summary"] = title

        return news_item

    def normalize_news(self, news_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize a list of news items by summarizing them and detecting related stories.

        Args:
            news_items: List of news items to normalize

        Returns:
            List of normalized news items
        """
        if not news_items:
            return []

        # First, summarize each news item
        normalized_items = []
        for item in news_items:
            # Create a copy of the item to avoid modifying the original
            normalized_item = item.copy()

            # Summarize the item
            summarized = self.summarize_news_item(normalized_item)

            # Generate a unique ID if not present
            if "id" not in summarized:
                summarized["id"] = str(uuid.uuid4())

            normalized_items.append(summarized)

        # Identify related stories
        if len(normalized_items) > 1 and self.embeddings:
            self._identify_related_stories(normalized_items)

        return normalized_items

    def _identify_related_stories(
        self, news_items: List[Dict[str, Any]], similarity_threshold: float = 0.75
    ):
        """
        Identify related news stories based on content similarity.

        Args:
            news_items: List of news items to analyze
            similarity_threshold: Threshold for considering stories related (0.0-1.0)
                                  Higher values mean more similarity required
        """
        # Get embeddings for all items
        try:
            titles = [item.get("title", "") for item in news_items]
            summaries = [item.get("summary", "") for item in news_items]

            # Combine title and summary for better representation
            texts = [f"{title}\n{summary}" for title, summary in zip(titles, summaries)]

            # Get embeddings
            embeddings = self.embeddings.embed_documents(texts)

            # Find related stories
            for i, item1 in enumerate(news_items):
                related_ids = []

                for j, item2 in enumerate(news_items):
                    if i != j:
                        # Calculate cosine similarity
                        similarity = 1 - cosine(embeddings[i], embeddings[j])

                        if similarity >= similarity_threshold:
                            related_ids.append(item2["id"])

                # Add related stories to item
                item1["related_stories"] = related_ids

        except Exception as e:
            print(f"Error identifying related stories: {e}")
            # Add empty related_stories list to all items
            for item in news_items:
                item["related_stories"] = []

    def group_similar_stories(
        self, news_items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Group similar news stories and create a representative for each group.

        Args:
            news_items: List of news items to group

        Returns:
            List of representative news items, one for each group of similar stories
        """
        if not news_items or len(news_items) <= 1:
            return news_items

        # First normalize if not already done
        normalized = []
        for item in news_items:
            if "summary" not in item:
                normalized.append(self.summarize_news_item(item))
            else:
                normalized.append(item)

        # Identify related stories if not already done
        if "related_stories" not in normalized[0] and self.embeddings:
            self._identify_related_stories(normalized)

        # Create a graph of related stories
        story_graph = defaultdict(set)
        for item in normalized:
            item_id = item["id"]
            related = item.get("related_stories", [])

            for related_id in related:
                story_graph[item_id].add(related_id)
                story_graph[related_id].add(item_id)

        # Find connected components (groups of related stories)
        visited = set()
        groups = []

        for item in normalized:
            item_id = item["id"]

            if item_id not in visited:
                # Start a new group
                group = []
                queue = [item_id]
                visited.add(item_id)

                # BFS to find all related stories
                while queue:
                    current_id = queue.pop(0)

                    # Find the item with this ID
                    current_item = next(
                        (i for i in normalized if i["id"] == current_id), None
                    )
                    if current_item:
                        group.append(current_item)

                    # Add related stories to queue
                    for related_id in story_graph[current_id]:
                        if related_id not in visited:
                            queue.append(related_id)
                            visited.add(related_id)

                groups.append(group)

        # Create representative for each group
        representatives = []
        for group in groups:
            if len(group) == 1:
                # Single item group
                representatives.append(group[0])
            else:
                # Multiple items - create a representative
                representative = self._create_group_representative(group)
                representatives.append(representative)

        return representatives

    def _create_group_representative(
        self, group: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create a representative news item for a group of similar stories.

        Args:
            group: List of similar news items

        Returns:
            Representative news item
        """
        # Sort by published date (newest first)
        sorted_group = sorted(
            group, key=lambda x: x.get("published_date", ""), reverse=True
        )

        # Use the most recent item as base
        representative = sorted_group[0].copy()

        # Collect all related story IDs
        all_related_ids = set()
        for item in group:
            all_related_ids.update(item.get("related_stories", []))
            all_related_ids.add(item["id"])

        # Remove self and any IDs from the group
        group_ids = {item["id"] for item in group}
        representative["related_stories"] = list(all_related_ids - group_ids)

        # Add source information
        representative["grouped_sources"] = [
            {
                "id": item["id"],
                "title": item.get("title", ""),
                "url": item.get("url", ""),
            }
            for item in group
        ]

        # Create a single coherent summary if there are multiple items
        if len(group) > 1:
            # Generate a prompt with all summaries
            all_summaries = "\n".join(
                [
                    f"Article {i+1}: {item.get('summary', item.get('title', ''))}"
                    for i, item in enumerate(
                        sorted_group[:3]
                    )  # Limit to top 3 for brevity
                ]
            )

            prompt = f"""
I have multiple news articles about the same topic. Here are summaries of the top articles:

{all_summaries}

Please create a single coherent summary that combines the most important information from all these articles in 3-4 sentences:
"""

            try:
                combined_summary = self.llm.invoke(prompt).strip()
                representative["summary"] = combined_summary
            except Exception as e:
                print(f"Error creating combined summary: {e}")
                # Use the summary from the most recent article as fallback
                pass

        return representative


# For testing purposes
if __name__ == "__main__":
    normalizer = NewsNormalizer()

    # Test summarization
    test_item = {
        "title": "Global Markets See Sharp Decline Amid Inflation Fears",
        "content": "Global markets experienced significant downturns today as new inflation data sparked concerns about central bank policies. Major indices in Asia, Europe, and the US all fell by at least 2%. The S&P 500 dropped 2.3%, while the Nasdaq Composite fell 3.1%. Analysts suggest this could impact economic growth in both developed and emerging markets. Some economists now predict central banks may need to raise interest rates more aggressively than previously anticipated. 'This is a clear signal that inflation pressures remain stubborn,' said Jane Smith, chief economist at XYZ Bank.",
    }

    summarized = normalizer.summarize_news_item(test_item)
    print(f"Original Title: {test_item['title']}")
    print(f"Summary: {summarized['summary']}")

    # Test similarity detection
    test_items = [
        {
            "id": "1",
            "title": "Tech Giant Announces New AI Chip",
            "content": "A leading technology company has unveiled a new AI chip that promises to deliver 50% better performance while using 30% less power. The chip will be available later this year.",
        },
        {
            "id": "2",
            "title": "New AI Processor Breaks Performance Records",
            "content": "A revolutionary AI processor was announced today, delivering unprecedented performance gains. The chip uses novel architecture to achieve better results while consuming less energy.",
        },
        {
            "id": "3",
            "title": "Senate Debates Infrastructure Bill",
            "content": "The US Senate continued debates over the infrastructure bill today, with key provisions being contested by both parties.",
        },
    ]

    normalized = normalizer.normalize_news(test_items)
    grouped = normalizer.group_similar_stories(normalized)

    print("\nNormalized and grouped stories:")
    for item in grouped:
        print(f"- {item['title']}")
        print(f"  Summary: {item.get('summary', 'No summary')}")
        if "grouped_sources" in item:
            print(f"  Combined from {len(item['grouped_sources'])} sources")
        print()
