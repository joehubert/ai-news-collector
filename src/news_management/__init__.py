"""
News Management Package

This package provides functionality for collecting and managing news.
It includes a wrapper for the Tavily API.
"""

from .tavily_wrapper import TavilyNewsWrapper

__all__ = ["TavilyNewsWrapper"]
