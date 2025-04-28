#!/bin/bash

# AI News Collector - Project Setup Script
echo "Setting up AI News Collector project structure..."

# Create main project directory
# mkdir -p ai_news_collector
# cd ai_news_collector

# Create Python virtual environment
echo "Creating Python virtual environment..."
python -m venv venv
echo "Virtual environment created. Activate it with: source venv/bin/activate"

# Create main project structure
mkdir -p src/news_management
mkdir -p src/content_management
mkdir -p src/user_interface
mkdir -p src/orchestration
mkdir -p data/chroma_db
mkdir -p data/user_interests
mkdir -p tests
mkdir -p docs

# Create initial files
touch README.md
touch requirements.txt
touch .env.example
touch .gitignore

# Create initial Python files for news management (MCP server)
touch src/news_management/__init__.py
touch src/news_management/mcp_server.py
touch src/news_management/tavily_wrapper.py

# Create initial Python files for content management
touch src/content_management/__init__.py
touch src/content_management/categorizer.py
touch src/content_management/vector_store.py
touch src/content_management/normalizer.py

# Create initial Python files for user interface
touch src/user_interface/__init__.py
touch src/user_interface/chatbot.py

# Create initial Python files for orchestration
touch src/orchestration/__init__.py
touch src/orchestration/langgraph_flow.py

# Create sample user interests file
echo "technology
renewable energy
artificial intelligence
python programming
climate change" > data/user_interests/sample_interests.txt

# Create initial main application file
touch src/main.py

# Write initial content to README.md
cat > README.md << 'EOL'
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
EOL

# Write initial content to requirements.txt
cat > requirements.txt << 'EOL'
# Core dependencies
langchain
langgraph
langchain-community
langserve
fastapi
uvicorn
pydantic
python-dotenv

# Vector database
chromadb

# News API
tavily-python

# LLM
ollama

# For MCP (Model Context Protocol)
mcp-python

# Testing
pytest
EOL

# Write initial content to .env.example
cat > .env.example << 'EOL'
# API Keys
TAVILY_API_KEY=your_tavily_api_key_here

# Configuration
OLLAMA_BASE_URL=http://localhost:11434
MODEL_NAME=llama3
EOL

# Write initial content to .gitignore
cat > .gitignore << 'EOL'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
ENV/
.env

# Distribution / packaging
dist/
build/
*.egg-info/

# Testing
.coverage
.pytest_cache/

# Data
data/chroma_db/*
!data/chroma_db/.gitkeep

# IDE specific files
.idea/
.vscode/
*.swp
*.swo
EOL

# Write initial main.py with basic structure
cat > src/main.py << 'EOL'
"""
AI News Collector - Main Application

This is the entry point for the AI News Collector application.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    """Main application entry point"""
    print("AI News Collector")
    print("=================")
    print("Starting application...")
    
    # TODO: Initialize components and start the application
    
    print("Application started. Type 'exit' to quit.")
    
    # Simple command loop
    while True:
        command = input("> ")
        if command.lower() == "exit":
            break
        
        # TODO: Process user commands using LangGraph

if __name__ == "__main__":
    main()
EOL

echo "Project structure has been set up successfully!"
echo "Next steps:"
echo "1. cd ai_news_collector"
echo "2. source venv/bin/activate  # Activate the virtual environment"
echo "3. pip install -r requirements.txt  # Install dependencies"
echo "4. Create a .env file with your API keys"
echo "5. Run the application: python src/main.py"