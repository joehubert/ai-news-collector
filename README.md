# AI News Collector

A tool to collect, categorize, and interact with recent news stories.

## Features
- Collects top news stories of the day
- Searches for news related to user interests
- Categorizes news into different sections
- Allows for summarization and Q&A about news stories

## Architecture
- News Management using Tavily and MCP server
- Content Management with categorization and vector storage
- Simple chatbot interface
- LangGraph for orchestration

## Setup
1. Clone this repository
2. Run `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and add your API keys
4. Add your interests to a file in `data/user_interests/`
5. Run `python src/main.py`
