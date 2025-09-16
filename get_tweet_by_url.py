from playwright.sync_api import sync_playwright
import json


def extract_tweet_id(tweet_url:str):
    """
    Given tweet_url, get the tweet_id
    For example: https://x.com/fundstrat/status/1967633474174713931 -> 1967633474174713931
    """
    sub_url = tweet_url.split("/")
    tweet_id = sub_url[-1]
    
    
    return tweet_id
def scrape_tweet(tweet_id):
    url = f"https://x.com/i/web/status/{tweet_id}"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # headless=True to hide browser
        page = browser.new_page()
        captured_data = None
        
        # Intercept API responses
        def handle_response(response):
            nonlocal captured_data
            if "TweetResultByRestId" in response.url and response.status == 200:
                try:
                    data = response.json()
                    captured_data = data
                except:
                    pass

        page.on("response", handle_response)

        # Load the tweet page
        page.goto(url)
        page.wait_for_timeout(5000)  # wait for network calls to finish

        browser.close()
        return captured_data
def get_tweet_from_json(json_file):
    data = json_file

    tweet = data["data"]["tweetResult"]["result"]

    # Main tweet info
    tweet_info = {
        "id": tweet["rest_id"],
        "user": tweet["core"]["user_results"]["result"]["core"]["screen_name"],
        "text": tweet["legacy"]["full_text"],
        "created_at": tweet["legacy"]["created_at"],
        "likes": tweet["legacy"]["favorite_count"],
        "retweets": tweet["legacy"]["retweet_count"],
        "replies": tweet["legacy"]["reply_count"],
        "quotes": tweet["legacy"]["quote_count"],
    }

    # Quoted/retweeted tweet info (if exists)
    quoted_info = None
    if "quoted_status_result" in tweet:
        quoted = tweet["quoted_status_result"]["result"]
        quoted_info = {
            "id": quoted["rest_id"],
            "user": quoted["core"]["user_results"]["result"]["core"]["screen_name"],
            "text": quoted["legacy"]["full_text"],
            "created_at": quoted["legacy"]["created_at"],
            "likes": quoted["legacy"]["favorite_count"],
            "retweets": quoted["legacy"]["retweet_count"],
            "replies": quoted["legacy"]["reply_count"],
            "quotes": quoted["legacy"]["quote_count"],
        }
    return tweet_info, quoted_info

# ... existing code ...

def extracting_tweet_info(tweet_url: str):
    """
    Extract tweet information from URL and return structured data for JSON serialization.
    
    Returns:
        Dictionary containing tweet data in JSON-serializable format
    """
    try:
        tweet_id = extract_tweet_id(tweet_url)
        json_response = scrape_tweet(tweet_id)
        tweet, quoted_tweet = get_tweet_from_json(json_response)
        
        result = {
            "success": True,
            "tweet_url": tweet_url,
            "tweet_count": 1,
            "tweets": [tweet]
        }
        
        # Add quoted tweet if it exists
        if quoted_tweet:
            result["quoted_tweets"] = [quoted_tweet]
            result["tweet_count"] = 2
        
        return result
        
    except Exception as e:
        print(f"Error at extracting tweets: {e}")
        return {
            "success": False,
            "error": str(e),
            "tweet_url": tweet_url,
            "tweet_count": 0,
            "tweets": []
        }

if __name__ == "__main__":
    extracting_tweet_info("https://x.com/fundstrat/status/1967633474174713931")
    # scrape_tweet("1967758095981097413")
