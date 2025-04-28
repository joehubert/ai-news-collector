"""
Test script for Tavily News Wrapper

This script tests the TavilyNewsWrapper component.
"""

import os
import sys
import json
from dotenv import load_dotenv

# Add the project root to the Python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Load environment variables from .env file
load_dotenv()

# Import the TavilyNewsWrapper
from src.news_management.tavily_wrapper import TavilyNewsWrapper


def test_tavily_wrapper():
    """Test the TavilyNewsWrapper functionality"""
    print("\n=== Testing TavilyNewsWrapper ===")

    # Create an instance of the wrapper
    wrapper = TavilyNewsWrapper()

    # Test reading interests from a file
    interests_file = os.path.join("data", "user_interests", "sample_interests.txt")
    interests = wrapper.read_interests_from_file(interests_file)
    print(f"Read {len(interests)} interests from {interests_file}: {interests}")

    # Test collecting top news
    print("\nCollecting top news (limited to 2 results for testing)...")
    top_news = wrapper.collect_top_news(max_results=2)
    print(f"Found {len(top_news)} top news stories:")
    for i, story in enumerate(top_news):
        print(f"{i+1}. {story['title']} - {story['url']}")

    # Test collecting news by interest
    if interests:
        interest = interests[0]
        print(f"\nCollecting news for interest: {interest} (limited to 1 result)...")
        interest_news = wrapper.collect_news_by_interest(interest, max_results=1)
        print(f"Found {len(interest_news)} news stories for {interest}:")
        for i, story in enumerate(interest_news):
            print(f"{i+1}. {story['title']} - {story['url']}")

    print("\nTavilyNewsWrapper tests completed!")
    return wrapper


if __name__ == "__main__":
    print("===== Testing Tavily News Wrapper =====")

    # Check if Tavily API key is set
    if not os.getenv("TAVILY_API_KEY"):
        print("Error: TAVILY_API_KEY environment variable not set.")
        print("Please set the TAVILY_API_KEY in the .env file.")
        exit(1)

    # Run the tests
    try:
        wrapper = test_tavily_wrapper()
        print("\nAll tests completed successfully!")
    except Exception as e:
        print(f"\nError during testing: {e}")
