from playwright.sync_api import sync_playwright
import json
import time


def extract_tweet_id(tweet_url: str):
    """
    Given tweet_url, get the tweet_id
    For example: https://x.com/fundstrat/status/1967633474174713931 -> 1967633474174713931
    """
    sub_url = tweet_url.split("/")
    tweet_id = sub_url[-1]
    return tweet_id


def scrape_tweet_and_thread(tweet_id):
    """
    Scrape a tweet and attempt to capture thread replies by the same user
    """
    url = f"https://x.com/i/web/status/{tweet_id}"
    
    max_retries = 3
    retry_delay = 5  # seconds
    
    for attempt in range(max_retries):
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                captured_data = {}
                
                # Intercept API responses
                def handle_response(response):
                    nonlocal captured_data
                    try:
                        if response.status == 200:
                            # Main tweet data
                            if "TweetResultByRestId" in response.url:
                                data = response.json()
                                captured_data['main_tweet'] = data
                            
                            # Thread/conversation data
                            elif "TweetDetail" in response.url:
                                data = response.json()
                                captured_data['thread_data'] = data
                                
                            # Additional conversation data
                            elif "conversation" in response.url.lower() or "ConversationThread" in response.url:
                                data = response.json()
                                captured_data['conversation'] = data
                                
                    except Exception as e:
                        print(f"Error parsing response: {e}")

                page.on("response", handle_response)

                # Load the tweet page and wait for content to load
                page.goto(url, timeout=30000)  # Increased timeout for page load
                page.wait_for_timeout(15000)  # Increased wait for initial content
                
                # Iteratively scroll to load all thread content
                last_height = page.evaluate("document.body.scrollHeight")
                while True:
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(3000)  # Wait for new content to load
                    new_height = page.evaluate("document.body.scrollHeight")
                    if new_height == last_height:
                        break
                    last_height = new_height

                browser.close()
                return captured_data
                
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                continue
            else:
                print("Max retries reached. Returning empty data.")
                return {}

    return {}


def extract_thread_from_data(captured_data, original_user):
    """
    Extract thread tweets by the same user from captured data
    """
    thread_tweets = []
    
    # Check different data sources for thread content
    for data_key in ['thread_data', 'conversation']:
        if data_key not in captured_data:
            continue
            
        data = captured_data[data_key]
        
        # Navigate through the data structure to find tweets
        try:
            # Look for instructions and entries that contain tweet data
            if 'data' in data:
                instructions = data.get('data', {}).get('threaded_conversation_with_injections_v2', {}).get('instructions', [])
                
                for instruction in instructions:
                    if instruction.get('type') == 'TimelineAddEntries':
                        entries = instruction.get('entries', [])
                        
                        for entry in entries:
                            content = entry.get('content', {})
                            
                            # Look for tweet content
                            if content.get('entryType') == 'TimelineTimelineItem':
                                item_content = content.get('itemContent', {})
                                if item_content.get('itemType') == 'TimelineTweet':
                                    tweet_results = item_content.get('tweet_results', {})
                                    if 'result' in tweet_results:
                                        tweet = tweet_results['result']
                                        
                                        # Check if it's by the same user
                                        tweet_user = tweet.get('core', {}).get('user_results', {}).get('result', {}).get('core', {}).get('screen_name', '')
                                        
                                        if tweet_user.lower() == original_user.lower():
                                            thread_tweets.append(tweet)
                                            
            # Also check legacy format
            elif 'globalObjects' in data:
                tweets = data.get('globalObjects', {}).get('tweets', {})
                for tweet_id, tweet_data in tweets.items():
                    user_id = tweet_data.get('user_id_str', '')
                    users = data.get('globalObjects', {}).get('users', {})
                    if user_id in users:
                        screen_name = users[user_id].get('screen_name', '')
                        if screen_name.lower() == original_user.lower():
                            thread_tweets.append({
                                'rest_id': tweet_id,
                                'legacy': tweet_data,
                                'core': {
                                    'user_results': {
                                        'result': {
                                            'core': {
                                                'screen_name': screen_name
                                            }
                                        }
                                    }
                                }
                            })
                            
        except Exception as e:
            print(f"Error extracting thread from {data_key}: {e}")
    
    return thread_tweets


def extract_full_text(tweet_data):
    """
    Extract the full text content from a tweet, including note_tweet content
    """
    # Start with the basic full_text
    full_text = tweet_data.get("legacy", {}).get("full_text", "")
    
    # Check if there's a note_tweet with expanded content
    if "note_tweet" in tweet_data:
        note_tweet_results = tweet_data["note_tweet"].get("note_tweet_results", {})
        if "result" in note_tweet_results:
            note_text = note_tweet_results["result"].get("text", "")
            # If note text is longer and more substantial, use it instead
            if len(note_text) > len(full_text):
                full_text = note_text
    
    return full_text


def get_tweet_from_json(json_file):
    """
    Extract main tweet and attempt to find thread by same user
    """
    main_data = json_file.get('main_tweet', json_file)
    data = main_data
    tweet = data["data"]["tweetResult"]["result"]

    # Extract full text (including note_tweet if present)
    main_text = extract_full_text(tweet)
    original_user = tweet["core"]["user_results"]["result"]["core"]["screen_name"]
    
    # Main tweet info
    tweet_info = {
        "id": tweet["rest_id"],
        "user": original_user,
        "text": main_text,
        "created_at": tweet["legacy"]["created_at"],
        "likes": tweet["legacy"]["favorite_count"],
        "retweets": tweet["legacy"]["retweet_count"],
        "replies": tweet["legacy"]["reply_count"],
        "quotes": tweet["legacy"]["quote_count"],
    }

    # Look for thread tweets by the same user
    thread_tweets = []
    if len(json_file) > 1:  # We have additional data beyond main tweet
        thread_data = extract_thread_from_data(json_file, original_user)
        
        # Process thread tweets
        for thread_tweet in thread_data:
            if thread_tweet.get('rest_id') != tweet_info['id']:  # Don't duplicate main tweet
                thread_text = extract_full_text(thread_tweet)
                if thread_text and len(thread_text.strip()) > 0:
                    thread_info = {
                        "id": thread_tweet["rest_id"],
                        "user": original_user,
                        "text": thread_text,
                        "created_at": thread_tweet["legacy"]["created_at"],
                        "likes": thread_tweet["legacy"].get("favorite_count", 0),
                        "retweets": thread_tweet["legacy"].get("retweet_count", 0),
                        "replies": thread_tweet["legacy"].get("reply_count", 0),
                        "quotes": thread_tweet["legacy"].get("quote_count", 0),
                    }
                    thread_tweets.append(thread_info)

    # Quoted/retweeted tweet info (if exists)
    quoted_info = None
    if "quoted_status_result" in tweet:
        quoted = tweet["quoted_status_result"]["result"]
        quoted_text = extract_full_text(quoted)
        
        quoted_info = {
            "id": quoted["rest_id"],
            "user": quoted["core"]["user_results"]["result"]["core"]["screen_name"],
            "text": quoted_text,
            "created_at": quoted["legacy"]["created_at"],
            "likes": quoted["legacy"]["favorite_count"],
            "retweets": quoted["legacy"]["retweet_count"],
            "replies": quoted["legacy"]["reply_count"],
            "quotes": quoted["legacy"]["quote_count"],
        }
    
    return tweet_info, quoted_info, thread_tweets


def combine_thread_content(main_tweet, thread_tweets):
    """
    Combine main tweet and thread tweets into a cohesive content
    """
    if not thread_tweets:
        return main_tweet
    
    # Sort thread tweets by creation time
    all_tweets = [main_tweet] + thread_tweets
    
    try:
        # Sort by tweet ID (newer tweets have higher IDs)
        all_tweets.sort(key=lambda x: int(x['id']))
    except:
        # Fallback: sort by created_at if available
        pass
    
    # Combine text content
    combined_text = ""
    for i, tweet in enumerate(all_tweets):
        if i == 0:
            combined_text = tweet['text']
        else:
            combined_text += f"\n\n[Thread {i+1}]: {tweet['text']}"
    
    # Create combined tweet object
    combined_tweet = main_tweet.copy()
    combined_tweet['text'] = combined_text
    combined_tweet['thread_count'] = len(all_tweets)
    combined_tweet['is_thread'] = True
    
    return combined_tweet


def extracting_tweet_info(tweet_url: str):
    """
    Extract tweet information from URL including thread content and return structured data for JSON serialization.
    
    Returns:
        Dictionary containing tweet data in JSON-serializable format
    """
    try:
        tweet_id = extract_tweet_id(tweet_url)
        json_response = scrape_tweet_and_thread(tweet_id)
        
        if not json_response or 'main_tweet' not in json_response:
            return {
                "success": False,
                "error": "Failed to scrape tweet data",
                "tweet_url": tweet_url,
                "tweet_count": 0,
                "tweets": []
            }
            
        tweet, quoted_tweet, thread_tweets = get_tweet_from_json(json_response)
        
        # Create result structure
        result = {
            "success": True,
            "tweet_url": tweet_url,
            "tweet_count": 1,
            "tweets": []
        }
        
        # Combine thread if it exists
        if thread_tweets:
            combined_tweet = combine_thread_content(tweet, thread_tweets)
            result["tweets"].append(combined_tweet)
            result["thread_info"] = {
                "is_thread": True,
                "thread_length": len(thread_tweets) + 1,
                "individual_tweets": [tweet] + thread_tweets
            }
            print(f"Found thread with {len(thread_tweets) + 1} tweets")
        else:
            result["tweets"].append(tweet)
        
        # Add quoted tweet if exists
        if quoted_tweet:
            result["quoted_tweets"] = [quoted_tweet]
            result["tweet_count"] += 1
        
        return result
        
    except Exception as e:
        print(f"Error at extracting tweets: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "tweet_url": tweet_url,
            "tweet_count": 0,
            "tweets": []
        }


if __name__ == "__main__":
    # Test with a tweet that might have a thread
    result = extracting_tweet_info("https://x.com/SebastienBubeck/status/1958198661139009862")
    print(json.dumps(result, indent=2))