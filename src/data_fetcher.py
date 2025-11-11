"""
Data fetcher module for retrieving and caching messages from local file or external API.
Loads from local messages_checkpoint.ndjson by default for performance.
Only fetches from API when explicitly requested via force_refresh=True.
"""
import requests
import time
import json
from pathlib import Path
from typing import List, Dict, Optional
from diskcache import Cache

# Handle both absolute and relative imports
try:
    from config import settings
    from logger import logger
    from models import Message
except ImportError:
    from .config import settings
    from .logger import logger
    from .models import Message


class DataFetcher:
    """Handles loading messages from local file or external API with caching."""
    
    def __init__(self, local_file: str = "messages_checkpoint.ndjson"):
        self.base_url = settings.api_base_url
        self.endpoint = settings.api_messages_endpoint
        self.cache = Cache(settings.cache_dir)
        self.cache_key = "all_messages"
        self.last_fetch_time = 0
        self.local_file = Path(local_file)
        
    def get_all_messages(self, force_refresh: bool = False, use_smart_fetch: bool = True) -> List[Dict]:
        """
        Get all messages. Priority order:
        1. Cache (if not force_refresh)
        2. Local ndjson file (if exists and not force_refresh)
        3. External API (only if force_refresh=True or no local data)
        
        Args:
            force_refresh: If True, fetch from external API instead of local file
            use_smart_fetch: If True, use multiple fetch strategies when fetching from API
            
        Returns:
            List of message dictionaries
        """
        # Check cache first (fastest)
        if not force_refresh:
            cached_data = self.cache.get(self.cache_key)
            if cached_data is not None:
                logger.info(f"Retrieved {len(cached_data)} messages from cache")
                return cached_data
        
        # Try loading from local file (second fastest, no network needed)
        if not force_refresh and self.local_file.exists():
            logger.info(f"Loading messages from local file: {self.local_file}")
            messages = self._load_from_local_file()
            if messages:
                # Cache the loaded messages
                self.cache.set(self.cache_key, messages, expire=settings.cache_ttl)
                logger.info(f"Loaded and cached {len(messages)} messages from local file")
                return messages
        
        # Only fetch from API if explicitly requested via force_refresh
        if force_refresh:
            logger.info("Fetching from external API (force_refresh=True)")
            if use_smart_fetch:
                all_messages = self._smart_fetch()
            else:
                all_messages = self._fetch_with_pagination()
            
            # Cache the results in memory ONLY (don't overwrite local file)
            # The local ndjson file remains the permanent source of truth
            self.cache.set(self.cache_key, all_messages, expire=settings.cache_ttl)
            self.last_fetch_time = time.time()
            logger.info(f"Successfully fetched and cached {len(all_messages)} messages from API (in-memory only)")
            logger.info(f"Note: Local file '{self.local_file}' remains unchanged")
            return all_messages
        else:
            logger.error(f"No local data file found at {self.local_file} and force_refresh=False")
            raise FileNotFoundError(
                f"Local data file not found: {self.local_file}. "
                "Use force_refresh=True to fetch from API or ensure the local file exists."
            )
    
    def _load_from_local_file(self) -> List[Dict]:
        """Load messages from local ndjson file."""
        messages = []
        try:
            with open(self.local_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line:
                        try:
                            msg = json.loads(line)
                            messages.append(msg)
                        except json.JSONDecodeError as e:
                            logger.warning(f"Skipping invalid JSON at line {line_num}: {e}")
                            continue
            logger.info(f"Loaded {len(messages)} messages from {self.local_file}")
            return messages
        except Exception as e:
            logger.error(f"Error loading from local file: {e}")
            return []
    
    def _fetch_with_pagination(self) -> List[Dict]:
        """Standard pagination-based fetching."""
        logger.info("Fetching messages using standard pagination...")
        all_messages = []
        skip = 0
        limit = 100  # API default
        
        try:
            while True:
                url = f"{self.base_url}{self.endpoint}"
                params = {"skip": skip, "limit": limit}
                
                try:
                    response = requests.get(url, params=params, timeout=30)
                    response.raise_for_status()
                except requests.exceptions.HTTPError as e:
                    if response.status_code in [400, 405, 500]:
                        # API has issues with pagination at certain points, stop here
                        logger.warning(f"API returned {response.status_code} at skip={skip}, stopping pagination. Fetched {len(all_messages)} messages so far.")
                        break
                    raise
                
                data = response.json()
                messages = data.get("items", [])
                total = data.get("total", 0)
                
                if not messages:
                    break
                    
                all_messages.extend(messages)
                logger.info(f"Fetched {len(all_messages)}/{total} messages")
                
                # Check if we've fetched all messages
                if len(all_messages) >= total:
                    break
                    
                skip += limit
                time.sleep(0.1)  # Rate limiting
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching messages: {e}")
            # Return cached data if available
            cached_data = self.cache.get(self.cache_key)
            if cached_data:
                logger.warning("Returning cached data due to API error")
                return cached_data
            raise
        
        return all_messages
    
    def _smart_fetch(self) -> List[Dict]:
        """
        Smart fetching strategy that tries multiple approaches:
        1. Fetch in smaller chunks with different skip values
        2. Try multiple starting points
        3. Collect unique messages
        """
        logger.info("Using smart fetch strategy to maximize data collection...")
        all_messages = {}  # Use dict to deduplicate by ID
        
        try:
            # Strategy 1: Fetch with dense skip increments to maximize coverage
            # Using steps of 10-50 to collect as much unique data as possible
            skip_increments = list(range(0, 2000, 25))  # Every 25 messages up to 2000
            
            for skip in skip_increments:
                try:
                    url = f"{self.base_url}{self.endpoint}"
                    params = {"skip": skip, "limit": 100}
                    
                    response = requests.get(url, params=params, timeout=30)
                    
                    if response.status_code in [400, 405, 500]:
                        logger.warning(f"API error at skip={skip}, trying next position")
                        continue
                        
                    response.raise_for_status()
                    data = response.json()
                    messages = data.get("items", [])
                    
                    # Add to dictionary (deduplicates automatically)
                    for msg in messages:
                        all_messages[msg['id']] = msg
                    
                    logger.info(f"Smart fetch: {len(all_messages)} unique messages collected (tried skip={skip})")
                    time.sleep(0.1)  # Rate limiting
                    
                except KeyboardInterrupt:
                    raise
                except Exception as e:
                    logger.warning(f"Error at skip={skip}: {e}")
                    continue
        except KeyboardInterrupt:
            logger.warning(f"Fetch interrupted! Collected {len(all_messages)} messages before interrupt")
            # Save what we have so far
            if all_messages:
                result = list(all_messages.values())
                self.cache.set(self.cache_key, result, expire=settings.cache_ttl)
                logger.info(f"Cached {len(result)} partial messages before exit")
            raise
        
        # Strategy 2: Try with different limit values at strategic positions
        # Only run if we haven't reached 1500 messages yet
        if len(all_messages) < 1500:
            logger.info("Trying alternative limit values at different positions...")
            try:
                for limit in [10, 20, 30, 50, 75]:
                    for skip in range(0, 1500, 100):
                        try:
                            url = f"{self.base_url}{self.endpoint}"
                            params = {"skip": skip, "limit": limit}
                            
                            response = requests.get(url, params=params, timeout=30)
                            if response.status_code == 200:
                                data = response.json()
                                messages = data.get("items", [])
                                for msg in messages:
                                    all_messages[msg['id']] = msg
                                
                            time.sleep(0.05)  # Faster rate limiting
                        except Exception as e:
                            continue
            except KeyboardInterrupt:
                logger.warning("Strategy 2 interrupted by user")
        else:
            logger.info(f"Skipping Strategy 2: already have {len(all_messages)} messages")
        
        result = list(all_messages.values())
        logger.info(f"Smart fetch completed: {len(result)} unique messages collected")
        return result
    
    def get_messages_by_user(self, user_name: str) -> List[Dict]:
        """Get all messages for a specific user."""
        all_messages = self.get_all_messages()
        user_messages = [
            msg for msg in all_messages 
            if msg.get("user_name", "").lower() == user_name.lower()
        ]
        return user_messages
    
    def fetch_user_messages_realtime(self, user_name: str, max_messages: int = 1000) -> List[Dict]:
        """
        Fetch messages for a specific user from the external API in real-time.
        Since the API doesn't support filtering by user, we fetch and filter locally.
        
        Args:
            user_name: Name of the user to fetch messages for
            max_messages: Maximum number of messages to fetch (default: 1000)
            
        Returns:
            List of messages from the specified user
        """
        logger.info(f"Fetching real-time messages for user: {user_name}")
        user_messages = []
        
        # Fetch in batches until we have enough messages for this user
        skip = 0
        limit = 100
        attempts = 0
        max_attempts = 20  # Don't try forever
        
        while len(user_messages) < max_messages and attempts < max_attempts:
            try:
                url = f"{self.base_url}{self.endpoint}"
                params = {"skip": skip, "limit": limit}
                
                response = requests.get(url, params=params, timeout=10)
                
                if response.status_code != 200:
                    logger.warning(f"API error at skip={skip}: {response.status_code}")
                    skip += limit
                    attempts += 1
                    continue
                
                data = response.json()
                messages = data.get("items", [])
                
                if not messages:
                    break  # No more messages
                
                # Filter for this user
                for msg in messages:
                    if msg.get('user_name', '').lower() == user_name.lower():
                        user_messages.append(msg)
                
                logger.info(f"Fetched {len(user_messages)} messages for {user_name} (tried skip={skip})")
                
                skip += limit
                attempts += 1
                time.sleep(0.05)  # Rate limiting
                
            except Exception as e:
                logger.warning(f"Error fetching at skip={skip}: {e}")
                skip += limit
                attempts += 1
                continue
        
        logger.info(f"Real-time fetch complete: {len(user_messages)} messages for {user_name}")
        return user_messages
    
    def search_messages(self, query: str) -> List[Dict]:
        """Simple text search in messages."""
        all_messages = self.get_all_messages()
        query_lower = query.lower()
        matching_messages = [
            msg for msg in all_messages
            if query_lower in msg.get("message", "").lower()
        ]
        return matching_messages
    
    def clear_cache(self):
        """
        Clear the in-memory cache.
        Next call to get_all_messages() will reload from local ndjson file.
        Note: This does NOT delete the local file - it remains as the source of truth.
        """
        self.cache.delete(self.cache_key)
        logger.info("In-memory cache cleared. Will reload from local file on next request.")


if __name__ == "__main__":
    # Test the data fetcher
    print("Testing Data Fetcher with Smart Fetch Strategy...")
    print("=" * 60)
    
    fetcher = DataFetcher()
    
    # Check if we have cached data first
    cached = fetcher.cache.get(fetcher.cache_key)
    if cached:
        print(f"\n✓ Found {len(cached)} messages in cache!")
        print("Clear cache with fetcher.clear_cache() if you want to refresh.\n")
        messages = cached
    else:
        # Clear cache to test fresh
        fetcher.clear_cache()
        
        # Fetch messages with smart strategy
        print("\nFetching messages...")
        try:
            messages = fetcher.get_all_messages(force_refresh=True, use_smart_fetch=True)
        except KeyboardInterrupt:
            print("\n\nInterrupted! Checking if partial data was saved...")
            cached = fetcher.cache.get(fetcher.cache_key)
            if cached:
                print(f"Partial data cached: {len(cached)} messages")
                messages = cached
            else:
                print("No data was cached before interrupt.")
                raise
    
    print(f"\n{'='*60}")
    print(f"RESULTS:")
    print(f"{'='*60}")
    print(f"Total unique messages collected: {len(messages)}")
    
    # Analyze users
    users = {}
    for msg in messages:
        user_name = msg['user_name']
        if user_name not in users:
            users[user_name] = 0
        users[user_name] += 1
    
    print(f"Unique users: {len(users)}")
    print(f"\nTop 10 most active users:")
    for user, count in sorted(users.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {user}: {count} messages")
    
    print(f"\n{'='*60}")
