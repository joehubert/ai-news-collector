# AI News Collector

## Overview

The purpose of this project is to collect top news stories of the day from the internet. The application will display headlines to the user and provide options to summarize any story. The app will also allow the user to ask questions about any of the stories. Additionally, the application will read a text file that lists interests of the user and search for recent news relatd to those topics. For the purposes of this application "recent news" will be any news stories released within the last day.

The project will demonstrate supporting technologies including:
* LLMs and Ollama
* AI Agents
* RAG
* Vector databases
* LangGraph
* MCP

## Functional Requirements

- The application will include a basic chatbot-type UI 
- A component of the application will run on a scheduled or triggered event and collect news stories from the internet.
- The application will persist the headlines and content of each news story to a vector database.
- If the application collects multiple articles about the same story, the application will display only headline for that story. All articles may be used to summarize content and answer user questions.
- The application will additionally categorize each story to one or more of these categories:
   - World News
   - US News
   - Sports News
   - Financial News
   - Technology News
   - Other News
- For simplicity and scalability reasons, the application will rebuild the contents of the database with each news collecction.
- The application will support these user-initiated actions:
    - The user can trigger the collection of news stories.
    - Seeing the numbered list of collected headlines, the user can request a summary of the story.
    - The user can ask questions about any news story in the list.
    - The user will manage a list of their interests in a text file available to the application. These interests will be used to generate internet searches for recent news stories on the topics.

## Technical Requirements

- The application will be written in Python.
- The application will be written a modular fashion so that different component responsibilities are isolated in different python files, etc.
- A simple Python UI library or framework will be used to create the UI.
- Tavily will be used to support the internet search.
- The file indicating the user's interest will be stored as: ./config/interests.md
- Chroma will be used as the vector database to store news content.
- LangGraph will be used to organize the flow of the application
- The news collector implemented as MCP server. This simplified MCP server will wrap the Tavily capabilities of searching as well as querying the vector database for the list of stories, for summaries per story, etc. Or should the web-searching and database querying be separate services/components?
- Ollama used to serve LLMs.
- llama3.2 will be the default model.
- A .env file will be used to hold all necessary access keys, default config options, etc.
