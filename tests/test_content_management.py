"""
Test script for Content Management Service

This script tests the ContentManagementService component.
"""

import os
import sys
import json
from dotenv import load_dotenv

# Add the project root to the Python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Load environment variables from .env file
load_dotenv()

# Import the ContentManagementService
from src.content_management.service import ContentManagementService


def test_content_management():
    """Test the ContentManagementService functionality"""
    print("\n=== Testing ContentManagementService ===")

    # Create an instance of the service
    service = ContentManagementService(reset_db=True)
    print("ContentManagementService initialized successfully!")

    # Test with sample news items
    test_items = [
        {
            "title": "Global Markets See Sharp Decline Amid Inflation Fears",
            "content": "Global markets experienced significant downturns today as new inflation data sparked concerns about central bank policies. Major indices in Asia, Europe, and the US all fell by at least 2%. The S&P 500 dropped 2.3%, while the Nasdaq Composite fell 3.1%.",
            "url": "https://example.com/markets",
            "published_date": "2023-01-01",
        },
        {
            "title": "Stock Markets Tumble Worldwide on Inflation Report",
            "content": "Stock markets around the world tumbled on Thursday following a higher-than-expected inflation report from the United States. The report indicated that inflation remains persistent despite central bank efforts to contain it.",
            "url": "https://example.com/stocks",
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
    print("\nProcessing news items...")
    result = service.process_news(test_items)
    print("Processing result:")
    print(f"Raw news items: {result['raw_count']}")
    print(f"Normalized news items: {result['normalized_count']}")
    print(f"Categories: {result['categories']}")

    # Test retrieval by category
    print("\nRetrieving news by category...")
    for category in ["financial", "technology", "us", "world", "sports", "other"]:
        news = service.get_news_by_category(category)
        print(f"{category.capitalize()} news: {len(news)} items")
        for item in news:
            print(f"- {item['title']}")

    # Test search
    print("\nSearching for news...")
    queries = ["markets", "technology", "infrastructure"]
    for query in queries:
        results = service.search_news(query)
        print(f"Results for '{query}': {len(results)} items")
        for item in results:
            print(f"- {item['title']} (Distance: {item['distance']:.4f})")

    print("\nContentManagementService tests completed!")
    return service


if __name__ == "__main__":
    print("===== Testing Content Management Service =====")

    # Run the tests
    try:
        service = test_content_management()
        print("\nAll tests completed successfully!")
    except Exception as e:
        print(f"\nError during testing: {e}")
