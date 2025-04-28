# AI News Collector - Project Requirements

## 1. Project Overview
   - Purpose and objectives: The purpose of this project is to collect top news stories of the day from the internet. The application will display headlines to the user and provide options to summarize any story. The app will also allow the user to ask questions about any of the stories. Additionally, the application will read a text file that lists interests of the user and search for recent news relatd to those topics. For the purposes of this application "recent news" will be any news stories released within the last day.
   - Key features summary
       - Collecting news stories
       - Summarizing news stories
       - Providing answers to questions on news stories
   - Technology stack overview
       - LLMs and Ollama
       - AI Agents
       - Retrieval Augmented Generation (RAG)
       - Vector databases (Chroma)
       - LangGraph
       - Model Context Protocol (MCP)

## 2. System Architecture
   - Component diagram
       - (to be generated later)
   - Data flow
       - (to be generated later)
   - Service interactions
       - (to be generated later)
   - Dependency diagram
       - (to be generated later)

## 3. Functional Requirements
   ### 3.1 News Management
   * The news management module will wrap Tavily functionality.
   * The news management module will be implemented as a simple MCP (Model Context Protocol) server.
   * The news management MCP server will support these tools:
       * collect-news: 
           * this tool will collect (using Tavily search) major news stories from the last day as well as stories from the last day that match user's interests
           * the story details will be persisted to a Chroma database using the content management service
           * the stories will be summarized and normalized with those results also persisted to a chroma database by the content management service
           * the stories will be categorized using the Content Management service
        * display-news-stories:
            * This tool will display the list of normalized headlines related to major stories and user's interests
            * This tool will take an optional parameter indicating the category of the news such as world, us, sports, finanical, etc
        * display-interesting-stories:
            * This tool will display only the stories that align with users interests
   
   ### 3.2 Content Management
   - Categorization methodology
       - An LLM will categorize each story with one or more of these categories:
         - World News
         - US News                
         - Sports News
         - Financial News
         - Technology News
         - Other News
   - This service will store the raw results from the news collection to the vector database
   - This service will normalize the raw results into summarized stories and store those results in the vector database

   ### 3.3 User Interface
   #### UI components and design
   The application will be a simple chatbot-type application.

   #### User interactions
   The user can type prompts that essentially tell the app to:
   * Collect news stories
   * Display a list of summary headlines
   * Answer a question about a story
   
   #### LangGraph Support
   * The application will use LangGraph to orchestrate the flow between the potential user prompts and the application behavior.
