import requests
import yaml
import os
import time
import logging
import random
from typing import List, Dict, Any
from urllib.parse import unquote
from html import unescape
import re
import orjson
from curl_cffi import requests as curl_requests
from tenacity import retry, stop_after_attempt, wait_exponential, wait_random, retry_if_exception_type, before_sleep_log, RetryError, after_log

# Set up logger
logger = logging.getLogger(__name__)

class SearchEngine:
    def __init__(self):
        self.config = self._load_config()
        self.primary_engine = self.config['search_engines']['primary']
        self.fallbacks = self.config['search_engines']['fallbacks']
        self.query_result = None
        
        # DuckDuckGo specific settings
        self.ddg_config = self.config.get('duckduckgo', {})
        self.request_delay = self.ddg_config.get('request_delay', 3.0)
        self.max_retries = self.ddg_config.get('max_retries', 5)
        self.timeout = self.ddg_config.get('timeout', 20)
        self.backoff_factor = self.ddg_config.get('backoff_factor', 2.0)
        self.jitter = self.ddg_config.get('jitter', True)
        self.rate_limit_window = self.ddg_config.get('rate_limit_window', 600)
        self.max_incidents_before_extended_backoff = self.ddg_config.get('max_incidents_before_extended_backoff', 3)
        self.extended_backoff_time = self.ddg_config.get('extended_backoff_time', 1800)
        self.daily_request_limit = self.ddg_config.get('daily_request_limit', 100)
        self.rotate_user_agent_every = self.ddg_config.get('rotate_user_agent_every', 2)
        self.ip_rotation_enabled = self.ddg_config.get('ip_rotation_enabled', True)
        self.ip_rotation_frequency = self.ddg_config.get('ip_rotation_frequency', 5)
        self.regions = self.ddg_config.get('regions', ["wt-wt", "us-en", "uk-en"])
        
        # Initialize tracking variables
        self.last_request_time = 0
        self.last_success_time = 0
        self.rate_limit_incidents = []
        self.extended_backoff_until = 0
        self.session_id = random.randint(1000000, 9999999)
        self.request_counter_file = os.path.join(os.path.dirname(__file__), '.ddg_request_counter')
        self.daily_request_count = self._load_request_count()
        self.request_count = 0
        self.used_user_agents = set()
        self.current_region_index = 0

    def _load_config(self):
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config.yaml')
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def _load_request_count(self):
        try:
            if os.path.exists(self.request_counter_file):
                with open(self.request_counter_file, 'r') as f:
                    data = f.read().strip().split(',')
                    if len(data) == 2:
                        date_str, count_str = data
                        today = time.strftime('%Y-%m-%d')
                        if date_str == today and count_str.isdigit():
                            return int(count_str)
        except Exception as e:
            logger.warning(f"Error loading request count: {e}")
        return 0

    def _save_request_count(self):
        try:
            today = time.strftime('%Y-%m-%d')
            with open(self.request_counter_file, 'w') as f:
                f.write(f"{today},{self.daily_request_count}")
        except Exception as e:
            logger.warning(f"Error saving request count: {e}")

    def _rotate_region(self):
        self.current_region_index = (self.current_region_index + 1) % len(self.regions)
        return self.regions[self.current_region_index]

    def _get_fresh_user_agent(self):
        ua_list = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36 Edg/92.0.902.78",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64; rv:90.0) Gecko/20100101 Firefox/90.0",
            "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
        ]
        
        available_user_agents = [ua for ua in ua_list if ua not in self.used_user_agents]
        
        if not available_user_agents and ua_list:
            recent_agents = list(self.used_user_agents)[-3:] if len(self.used_user_agents) > 3 else self.used_user_agents
            self.used_user_agents = set(recent_agents)
            available_user_agents = [ua for ua in ua_list if ua not in self.used_user_agents]
        
        if available_user_agents:
            selected_ua = random.choice(available_user_agents)
            self.used_user_agents.add(selected_ua)
            return selected_ua
            
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36"

    def _is_rate_limit_error(self, exception):
        error_str = str(exception).lower()
        return any(term in error_str for term in ["rate", "limit", "429", "too many requests", "ratelimit", "202", "blocked"])

    def _record_rate_limit_incident(self):
        now = time.time()
        self.rate_limit_incidents.append(now)
        self.rate_limit_incidents = [t for t in self.rate_limit_incidents if now - t <= self.rate_limit_window]
        
        if len(self.rate_limit_incidents) >= self.max_incidents_before_extended_backoff:
            logger.warning(f"Too many rate limit incidents ({len(self.rate_limit_incidents)}). Enabling extended backoff.")
            self.extended_backoff_until = now + self.extended_backoff_time

    def _should_apply_extended_backoff(self):
        return time.time() < self.extended_backoff_until

    def _get_success_interval(self):
        if self.last_success_time == 0:
            return float('inf')
        return time.time() - self.last_success_time

    def _random_jitter(self, base=1, deviation=2):
        return random.uniform(base, base + deviation)

    def search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        logger.info(f"Executing search for query: {query}")
        
        # Check daily request limit
        if self.daily_request_count >= self.daily_request_limit:
            logger.warning(f"Daily request limit of {self.daily_request_limit} reached.")
            return self._generate_placeholder_results(query, max_results)
            
        # Check if we're in extended backoff period
        if self._should_apply_extended_backoff():
            remaining = int(self.extended_backoff_until - time.time())
            logger.warning(f"In extended backoff period for {remaining}s.")
            return self._generate_placeholder_results(query, max_results)

        # Try primary engine first (DuckDuckGo)
        try:
            if self.primary_engine == "duckduckgo":
                return self._duckduckgo_search(query, max_results)
        except Exception as e:
            logger.error(f"Primary search engine failed: {str(e)}")

        # Try fallback engines if primary fails
        for engine, config in self.fallbacks.items():
            if config['enabled']:
                try:
                    if engine == "tavily":
                        return self._tavily_search(query, config['api_key'], max_results)
                    elif engine == "google":
                        return self._google_search(query, config['api_key'], config['search_engine_id'], max_results)
                except Exception as e:
                    logger.error(f"Fallback engine {engine} failed: {str(e)}")
                    continue

        raise Exception("All search engines failed")

    def _duckduckgo_search(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        session = curl_requests.Session(impersonate="chrome", allow_redirects=False)
        session.headers["Referer"] = "https://duckduckgo.com/"

        # Get initial page to get vqd
        resp = session.post("https://duckduckgo.com/", data={"q": query})
        if resp.status_code != 200:
            raise Exception(f"DuckDuckGo request failed with status {resp.status_code}")

        vqd = self._extract_vqd(resp.content)
        if not vqd:
            raise Exception("Could not extract vqd from DuckDuckGo response")

        # Get search results
        params = {
            "q": query,
            "kl": self._rotate_region(),
            "p": "1",
            "s": "0",
            "df": "",
            "vqd": vqd,
            "ex": ""
        }
        
        # Rotate user agent if needed
        if self.request_count % self.rotate_user_agent_every == 0:
            user_agent = self._get_fresh_user_agent()
            if user_agent:
                session.headers["User-Agent"] = user_agent

        resp = session.get("https://links.duckduckgo.com/d.js", params=params)
        if resp.status_code != 200:
            raise Exception(f"DuckDuckGo search failed with status {resp.status_code}")

        page_data = self._text_extract_json(resp.content)
        if not page_data:
            raise Exception("Could not extract search results from DuckDuckGo response")

        results = []
        for row in page_data:
            href = row.get("u")
            if href and href != f"http://www.google.com/search?q={query}":
                body = self._normalize(row["a"])
                if body:
                    result = {
                        "title": self._normalize(row["t"]),
                        "href": self._normalize_url(href),
                        "body": body,
                    }
                    results.append(result)
                    
                    if len(results) >= max_results:
                        break

        self.query_result = results
        self.last_success_time = time.time()
        self.request_count += 1
        self.daily_request_count += 1
        self._save_request_count()
        
        return results

    def _tavily_search(self, query: str, api_key: str, max_results: int = 10) -> List[Dict[str, Any]]:
        headers = {
            "X-Api-Key": api_key,
            "Content-Type": "application/json"
        }
        data = {
            "query": query,
            "search_depth": "basic",
            "max_results": max_results
        }
        
        response = requests.post(
            "https://api.tavily.com/search",
            headers=headers,
            json=data
        )
        
        if response.status_code != 200:
            raise Exception(f"Tavily API request failed with status {response.status_code}")
            
        results = response.json()["results"]
        self.query_result = [{
            "title": result["title"],
            "href": result["url"],
            "body": result["content"]
        } for result in results]
        
        return self.query_result

    def _google_search(self, query: str, api_key: str, search_engine_id: str, max_results: int = 10) -> List[Dict[str, Any]]:
        params = {
            "key": api_key,
            "cx": search_engine_id,
            "q": query
        }
        
        response = requests.get(
            "https://www.googleapis.com/customsearch/v1",
            params=params
        )
        
        if response.status_code != 200:
            raise Exception(f"Google API request failed with status {response.status_code}")
            
        results = response.json().get("items", [])
        self.query_result = [{
            "title": result["title"],
            "href": result["link"],
            "body": result.get("snippet", "")
        } for result in results]
        
        return self.query_result

    def get_first_link(self):
        if not self.query_result:
            return None
        return self.query_result[0]["href"]

    @staticmethod
    def _extract_vqd(html_bytes: bytes) -> str:
        patterns = [(b'vqd="', 5, b'"'), (b"vqd=", 4, b"&"), (b"vqd='", 5, b"'")]
        for start_pattern, offset, end_pattern in patterns:
            try:
                start = html_bytes.index(start_pattern) + offset
                end = html_bytes.index(end_pattern, start)
                return html_bytes[start:end].decode()
            except ValueError:
                continue
        return None

    @staticmethod
    def _text_extract_json(html_bytes):
        try:
            start = html_bytes.index(b"DDG.pageLayout.load('d',") + 24
            end = html_bytes.index(b");DDG.duckbar.load(", start)
            return orjson.loads(html_bytes[start:end])
        except Exception as ex:
            logger.error(f"Error extracting JSON: {type(ex).__name__}: {ex}")
            return None

    @staticmethod
    def _normalize_url(url: str) -> str:
        return unquote(url.replace(" ", "+")) if url else ""

    @staticmethod
    def _normalize(raw_html: str) -> str:
        return unescape(re.sub("<.*?>", "", raw_html)) if raw_html else ""

    def _generate_placeholder_results(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        results = []
        for i in range(max_results):
            results.append({
                "title": f"Search result {i+1} for '{query}'" if i == 0 else f"Alternative search result for '{query}'",
                "body": "Search could not be completed. Please try again later or refine your search query.",
                "href": "https://duckduckgo.com/?q=" + query.replace(" ", "+")
            })
        return results
