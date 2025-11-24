"""
================================================================================
search_engine.py - Web Search Engine for Stealth Deck
================================================================================
Version: 1.0.0
Date: 2025-11-24
Author: Stealth Deck Project
License: MIT

================================================================================
DESCRIPTION:
Headless web search scraper for Google search results.
Provides discreet web search capability without browser.

Features:
- Google search scraping
- Result parsing
- User-agent rotation
- Rate limiting
- Result caching
- Error handling

================================================================================
"""

import logging
import requests
import time
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import random


class SearchResult:
    """Represents a single search result."""
    
    def __init__(self, title: str, url: str, snippet: str):
        """
        Initialize search result.
        
        Args:
            title: Result title
            url: Result URL
            snippet: Result description
        """
        self.title = title
        self.url = url
        self.snippet = snippet
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary."""
        return {
            'title': self.title,
            'url': self.url,
            'snippet': self.snippet
        }


class SearchEngine:
    """
    Web search engine using Google scraping.
    
    Performs headless Google searches and parses results.
    """
    
    def __init__(self):
        """Initialize search engine."""
        self.logger = logging.getLogger('search_engine')
        
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
        ]
        
        self.timeout = 10
        self.max_results = 5
        self.rate_limit_delay = 2.0
        self.last_search_time = 0.0
        
        self.cache: Dict[str, List[SearchResult]] = {}
        self.cache_ttl = 1800
    
    def search(self, query: str, max_results: Optional[int] = None) -> List[SearchResult]:
        """
        Perform web search.
        
        Args:
            query: Search query
            max_results: Maximum results to return
            
        Returns:
            List of search results
        """
        if max_results is None:
            max_results = self.max_results
        
        cache_key = f"{query}:{max_results}"
        if cache_key in self.cache:
            self.logger.debug("Returning cached results")
            return self.cache[cache_key]
        
        self._rate_limit()
        
        try:
            self.logger.info(f"Searching: {query}")
            
            results = self._scrape_google(query, max_results)
            
            self.cache[cache_key] = results
            
            self.logger.info(f"Found {len(results)} results")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return []
    
    def _scrape_google(self, query: str, max_results: int) -> List[SearchResult]:
        """
        Scrape Google search results.
        
        Args:
            query: Search query
            max_results: Maximum results
            
        Returns:
            List of results
        """
        encoded_query = quote_plus(query)
        url = f"https://www.google.com/search?q={encoded_query}&num={max_results}"
        
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        response = requests.get(url, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        
        for div in soup.find_all('div', class_='g'):
            try:
                title_elem = div.find('h3')
                link_elem = div.find('a')
                snippet_elem = div.find('div', class_=['VwiC3b', 'yXK7lf'])
                
                if title_elem and link_elem:
                    title = title_elem.get_text()
                    url = link_elem.get('href', '')
                    
                    if url.startswith('/url?q='):
                        url = url.split('/url?q=')[1].split('&')[0]
                    
                    snippet = ''
                    if snippet_elem:
                        snippet = snippet_elem.get_text()
                    
                    if url and not url.startswith('/search'):
                        result = SearchResult(title, url, snippet)
                        results.append(result)
                        
                        if len(results) >= max_results:
                            break
                            
            except Exception as e:
                self.logger.debug(f"Error parsing result: {e}")
                continue
        
        return results
    
    def search_and_format(self, query: str, max_results: Optional[int] = None) -> str:
        """
        Search and format results as text.
        
        Args:
            query: Search query
            max_results: Maximum results
            
        Returns:
            Formatted results string
        """
        results = self.search(query, max_results)
        
        if not results:
            return "No results found."
        
        output = f"Search results for: {query}\n\n"
        
        for i, result in enumerate(results, 1):
            output += f"{i}. {result.title}\n"
            output += f"   {result.url}\n"
            if result.snippet:
                output += f"   {result.snippet}\n"
            output += "\n"
        
        return output
    
    def _rate_limit(self) -> None:
        """Apply rate limiting between searches."""
        current_time = time.time()
        time_since_last = current_time - self.last_search_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            self.logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        self.last_search_time = time.time()
    
    def clear_cache(self) -> None:
        """Clear search cache."""
        self.cache.clear()
        self.logger.info("Search cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get search engine statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            'cache_size': len(self.cache),
            'timeout': self.timeout,
            'max_results': self.max_results,
            'rate_limit_delay': self.rate_limit_delay
        }


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    search = SearchEngine()
    
    results = search.search("Python programming", max_results=3)
    
    for i, result in enumerate(results, 1):
        print(f"{i}. {result.title}")
        print(f"   {result.url}")
        print(f"   {result.snippet}\n")
