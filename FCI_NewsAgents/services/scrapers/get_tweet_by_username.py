import requests
import json
import hmac
import hashlib
import base64
import urllib.parse
import time
import secrets
from typing import Dict, List, Optional
import os
import dotenv
class TwitterAPIClient:
    def __init__(self, bearer_token: str, access_token: str, access_token_secret: str, consumer_key: str = None, consumer_secret: str = None):
        """
        Initialize Twitter API client with credentials.
        
        Args:
            bearer_token: Bearer token for API v2 (recommended)
            access_token: OAuth 1.0a access token
            access_token_secret: OAuth 1.0a access token secret
            consumer_key: OAuth 1.0a consumer key (required for OAuth 1.0a)
            consumer_secret: OAuth 1.0a consumer secret (required for OAuth 1.0a)
        """
        self.bearer_token = bearer_token
        self.access_token = access_token
        self.access_token_secret = access_token_secret
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.base_url_v2 = "https://api.twitter.com/2"
        self.base_url_v1 = "https://api.twitter.com/1.1"

    def _handle_rate_limit(self, response: requests.Response) -> Optional[int]:
        """
        Handle rate limit response and return wait time in seconds.
        
        Args:
            response: HTTP response object
            
        Returns:
            Wait time in seconds, or None if not rate limited
        """
        if response.status_code == 429:
            # Check for rate limit reset time in headers
            reset_time = response.headers.get('x-rate-limit-reset')
            if reset_time:
                wait_time = int(reset_time) - int(time.time())
                return max(wait_time, 60)  # Wait at least 1 minute
            else:
                return 900  # Default wait 15 minutes if no reset time
        return None

    def _make_request_with_retry(self, method: str, url: str, headers: Dict, params: Dict = None, max_retries: int = 3) -> Dict:
        """
        Make HTTP request with automatic retry on rate limits.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            headers: Request headers
            params: Request parameters
            max_retries: Maximum number of retries
            
        Returns:
            Response data or error dictionary
        """
        for attempt in range(max_retries + 1):
            try:
                if method.upper() == 'GET':
                    response = requests.get(url, headers=headers, params=params, timeout=30)
                else:
                    response = requests.request(method, url, headers=headers, params=params, timeout=30)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    wait_time = self._handle_rate_limit(response)
                    if attempt < max_retries and wait_time:
                        print(f"Rate limited. Waiting {wait_time} seconds before retry {attempt + 1}/{max_retries}...")
                        time.sleep(min(wait_time, 60))  # Cap wait time at 1 minute for user experience
                        continue
                    else:
                        return {
                            "error": f"Rate limit exceeded. Try again in {wait_time} seconds.",
                            "retry_after": wait_time
                        }
                else:
                    return {"error": f"API request failed: {response.status_code} - {response.text}"}
                    
            except requests.exceptions.Timeout:
                if attempt < max_retries:
                    print(f"Request timeout. Retrying {attempt + 1}/{max_retries}...")
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    return {"error": "Request timeout after all retries"}
            except requests.exceptions.RequestException as e:
                return {"error": f"Request failed: {str(e)}"}
        
        return {"error": "Max retries exceeded"}
        
    def get_user_tweets_v2(self, username: str, max_results: int = 10, tweet_fields: List[str] = None) -> Dict:
        """
        Fetch user tweets using Twitter API v2 with Bearer Token authentication.
        
        Args:
            username: Twitter username (without @)
            max_results: Number of tweets to fetch (5-100, will be adjusted if outside range)
            tweet_fields: Additional tweet fields to include
            
        Returns:
            Dictionary containing tweets data
        """
        if tweet_fields is None:
            tweet_fields = ["created_at", "public_metrics", "author_id", "context_annotations"]
        
        # First, get user ID from username
        user_url = f"{self.base_url_v2}/users/by/username/{username}"
        user_headers = {
            "Authorization": f"Bearer {self.bearer_token}"
        }
        
        print("Getting user info...")
        user_data = self._make_request_with_retry("GET", user_url, user_headers)
        if "error" in user_data:
            return {"error": f"Failed to get user info: {user_data['error']}"}
        
        if "data" not in user_data:
            return {"error": "User not found"}
            
        user_id = user_data["data"]["id"]
        
        # Now get user's tweets
        tweets_url = f"{self.base_url_v2}/users/{user_id}/tweets"
        params = {
            "max_results": max(5, min(max_results, 100)),  # Ensure minimum of 5
            "tweet.fields": ",".join(tweet_fields)
        }
        
        headers = {
            "Authorization": f"Bearer {self.bearer_token}"
        }
        
        print("Fetching tweets...")
        return self._make_request_with_retry("GET", tweets_url, headers, params)

    def _generate_oauth_signature(self, method: str, url: str, params: Dict[str, str]) -> str:
        """Generate OAuth 1.0a signature for API v1.1 requests."""
        # Create signature base string
        sorted_params = sorted(params.items())
        param_string = "&".join([f"{k}={urllib.parse.quote(str(v), safe='')}" for k, v in sorted_params])
        
        base_string = f"{method.upper()}&{urllib.parse.quote(url, safe='')}&{urllib.parse.quote(param_string, safe='')}"
        
        signing_key = f"{urllib.parse.quote(self.consumer_secret or '', safe='')}&{urllib.parse.quote(self.access_token_secret, safe='')}"
        
        signature = base64.b64encode(
            hmac.new(signing_key.encode(), base_string.encode(), hashlib.sha1).digest()
        ).decode()
        
        return signature

    def get_user_tweets_v1(self, screen_name: str, count: int = 20) -> Dict:
        """
        Fetch user tweets using Twitter API v1.1 with OAuth 1.0a authentication.
        
        Args:
            screen_name: Twitter username (without @)
            count: Number of tweets to fetch (1-200)
            
        Returns:
            Dictionary containing tweets data
        """
        if not self.consumer_key or not self.consumer_secret:
            return {"error": "Consumer key and secret required for OAuth 1.0a authentication"}
        
        url = f"{self.base_url_v1}/statuses/user_timeline.json"
        
        oauth_params = {
            "oauth_consumer_key": self.consumer_key,
            "oauth_token": self.access_token,
            "oauth_signature_method": "HMAC-SHA1",
            "oauth_timestamp": str(int(time.time())),
            "oauth_nonce": secrets.token_hex(16),
            "oauth_version": "1.0",
            "screen_name": screen_name,
            "count": min(count, 200),
            "include_rts": "false",
            "exclude_replies": "false"
        }
        
        oauth_params["oauth_signature"] = self._generate_oauth_signature("GET", url, oauth_params)
        
        auth_params = {k: v for k, v in oauth_params.items() if k.startswith("oauth_")}
        auth_header = "OAuth " + ", ".join([f'{k}="{urllib.parse.quote(str(v), safe="")}"' for k, v in auth_params.items()])
        
        headers = {
            "Authorization": auth_header
        }
        
        params = {
            "screen_name": screen_name,
            "count": max(1, min(count, 200)),  # API v1.1 allows 1-200
            "include_rts": "false",
            "exclude_replies": "false"
        }
        
        print("Making OAuth 1.0a request...")
        return self._make_request_with_retry("GET", url, headers, params)


def fetch_tweets_by_username(username: str, num_posts: int = 5):
    """
    Fetch tweets by username and return structured data for JSON serialization.
    
    Returns:
        Dictionary containing tweet data in JSON-serializable format
    """
    dotenv.load_dotenv()
    BEARER_TOKEN = os.getenv("x_bearer_token")
    ACCESS_TOKEN = os.getenv("x_access_token")
    ACCESS_TOKEN_SECRET = os.getenv("x_access_token_secret")
    
    # Optional: For OAuth 1.0a (API v1.1)
    CONSUMER_KEY = os.getenv("consumer_key")  
    CONSUMER_SECRET = os.getenv("consumer_secret")  
    
    # Initialize client
    client = TwitterAPIClient(
        bearer_token=BEARER_TOKEN,
        access_token=ACCESS_TOKEN,
        access_token_secret=ACCESS_TOKEN_SECRET,
        consumer_key=CONSUMER_KEY,
        consumer_secret=CONSUMER_SECRET
    )
    
    print(f"Fetching tweets for @{username}...")
    
    # Try API v2 first (recommended)
    tweets_data = client.get_user_tweets_v2(username, max_results=num_posts)
    
    if "error" in tweets_data:
        print(f"API v2 failed: {tweets_data['error']}")
        print("Trying API v1.1...")
        
        # Fallback to API v1.1
        tweets_data = client.get_user_tweets_v1(username, count=num_posts)
    
    if "error" in tweets_data:
        print(f"Error: {tweets_data['error']}")
        if "retry_after" in tweets_data:
            print(f"You can try again in {tweets_data['retry_after']} seconds.")
        return {
            "success": False,
            "error": tweets_data['error'],
            "username": username,
            "tweet_count": 0,
            "tweets": []
        }
    
    result = {
        "success": True,
        "username": username,
        "tweet_count": 0,
        "tweets": []
    }
    
    if "data" in tweets_data and tweets_data["data"]:
        tweets = tweets_data["data"]
        print(f"\nFound {len(tweets)} tweets:\n")
        
        processed_tweets = []
        for i, tweet in enumerate(tweets, 1):
            if isinstance(tweet, dict):
                tweet_text = tweet.get("text") or tweet.get("full_text", "")
                tweet_id = tweet.get("id") or tweet.get("id_str", "")
                created_at = tweet.get("created_at", "")
                
                # Standardize tweet format
                processed_tweet = {
                    "id": str(tweet_id),
                    "user": username,
                    "text": tweet_text,
                    "created_at": created_at,
                    "likes": 0,
                    "retweets": 0,
                    "replies": 0,
                    "quotes": 0
                }
                
                # Add metrics if available
                if "public_metrics" in tweet:
                    metrics = tweet["public_metrics"]
                    processed_tweet.update({
                        "likes": metrics.get("like_count", 0),
                        "retweets": metrics.get("retweet_count", 0),
                        "replies": metrics.get("reply_count", 0),
                        "quotes": metrics.get("quote_count", 0)
                    })
                elif "favorite_count" in tweet:  # API v1.1 format
                    processed_tweet.update({
                        "likes": tweet.get("favorite_count", 0),
                        "retweets": tweet.get("retweet_count", 0),
                        "replies": tweet.get("reply_count", 0)
                    })
                
                processed_tweets.append(processed_tweet)
                
                # Print for immediate feedback
                # print(f"Tweet {i}:")
                # print(f"ID: {tweet_id}")
                # print(f"Created: {created_at}")
                # print(f"Text: {tweet_text}")
                # print(f"Likes: {processed_tweet['likes']}, "
                #       f"Retweets: {processed_tweet['retweets']}, "
                #       f"Replies: {processed_tweet['replies']}")
                # print("-" * 80)
        
        result["tweets"] = processed_tweets
        result["tweet_count"] = len(processed_tweets)
    else:
        print("No tweets found or empty response.")
    
    return result


if __name__ == "__main__":
    username = "elonmusk"
    result = fetch_tweets_by_username(username)
    print(result)