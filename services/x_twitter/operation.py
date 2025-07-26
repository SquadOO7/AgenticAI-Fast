import httpx
from fastapi import HTTPException, status
from datetime import datetime, timedelta, timezone
from services.x_twitter.query import COMPREHENSIVE_QUERY
import requests
from utilities.help_func import GlobalState
from google.cloud import pubsub_v1
from google.oauth2 import service_account
import json
import random

glob = GlobalState()


async def get_user_id(username: str):
    BASE_URL=glob.env.get("BASE_URL")
    HEADERS={'authorization': f'Bearer {glob.env.get("X_BEARER_TOKEN")}'}
    async with httpx.AsyncClient() as client:
        url = f"{BASE_URL}/users/by/username/{username}"
        response = await client.get(url, headers=HEADERS)
        print(response.json())
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Failed to get user ID for {username}")
        return response.json()["data"]["id"]

async def get_user_tweets(user_id: str, start_time: str, end_time: str):
    BASE_URL=glob.env.get("BASE_URL")
    HEADERS={'authorization': f'Bearer {glob.env.get("X_BEARER_TOKEN")}'}
    tweets = []
    params = {
        "max_results": 100,
        "tweet.fields": "created_at,lang,text",
        "start_time": start_time,
        "end_time": end_time
    }
    url = f"{BASE_URL}/users/{user_id}/tweets"
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=HEADERS, params=params)
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Failed to get tweets for user {user_id}")
        print(response.json())
        for tweet in response.json().get("data", []):
            tweets.append(tweet)
    return tweets



def get_date_range_for_last_7_days():
    end_time = datetime.now(timezone.utc) - timedelta(seconds=10)
    start_time = end_time - timedelta(days=7)

    start_time_str = start_time.isoformat(timespec="seconds").replace("+00:00", "Z")
    end_time_str = end_time.isoformat(timespec="seconds").replace("+00:00", "Z")

    return start_time_str, end_time_str

def fetch_bengaluru_feeds_from_x():
    """
    Fetches tweets related to Bengaluru for the specified categories
    from the last 7 days using X API v2.
    Handles pagination to retrieve up to 500 tweets.
    """
    BASE_URL=glob.env.get("BASE_URL")
    HEADERS={'authorization': f'Bearer {glob.env.get("X_BEARER_TOKEN")}'}
    all_feeds = []
    next_token = None
    page_count = 0
    max_pages = 2

    start_time, end_time = get_date_range_for_last_7_days()
    print(f"Fetching tweets from: {start_time} to {end_time}")

    while True:
        page_count += 1
        if page_count == max_pages:
            print(f"Reached maximum pages ({max_pages}). Stopping pagination.")
            break

        print(f"\nFetching page {page_count}...")
        current_params = {
            "query": COMPREHENSIVE_QUERY,
            "tweet.fields": "created_at,text,author_id,public_metrics,geo",
            "start_time": start_time,
            "end_time": end_time,
            "max_results": 100
        }
        if next_token:
            current_params["next_token"] = next_token

        try:
            URL = BASE_URL+"/tweets/search/recent"
            response = requests.get(URL, headers=HEADERS, params=current_params)
            response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
            data = response.json()

            if "data" in data:
                for tweet in data["data"]:
                    # Basic categorization based on keywords in the tweet text
                    # More sophisticated categorization would involve NLP for better accuracy
                    category = "general"
                    text_lower = tweet['text'].lower()
                    if any(k in text_lower for k in ["crime", "theft", "robbery", "police", "arrest", "fir"]):
                        category = "crime"
                    elif any(k in text_lower for k in ["news", "update", "latest", "report", "breaking"]):
                        category = "local news"
                    elif any(k in text_lower for k in ["weather", "rain", "forecast", "monsoon", "sunny", "temperature"]):
                        category = "weather"
                    elif any(k in text_lower for k in ["civic", "bbmp", "garbage", "drainage", "power cut", "water supply", "yehthikkarkedikhao", "citizen", "complaint"]):
                        category = "civic"
                    elif any(k in text_lower for k in ["pothole", "road condition", "fixmyroad", "bad road"]):
                        category = "potholes"
                    elif any(k in text_lower for k in ["traffic", "jam", "road block", "commute", "congestion"]):
                        category = "traffic"

                    all_feeds.append({
                        "id": tweet.get("id"),
                        "category": category,
                        "text": tweet.get("text"),
                        "created_at": tweet.get("created_at"),
                        "author_id": tweet.get("author_id"),
                        "public_metrics": tweet.get("public_metrics", {}),
                        "geo": tweet.get("geo", {})
                    })
                print(f"  Fetched {len(data['data'])} tweets.")
            else:
                print("  No 'data' field in response for this page.")

            # Check for pagination token
            if "next_token" in data.get("meta", {}):
                next_token = data["meta"]["next_token"]
            else:
                next_token = None

            if not next_token:
                print("No more pages to fetch.")
                break

        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err} - {response.text}")
            raise HTTPException(status_code=response.status_code, detail=f"X API Error: {response.text}")
        except requests.exceptions.ConnectionError as conn_err:
            print(f"Connection error occurred: {conn_err}")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Could not connect to X API.")
        except requests.exceptions.Timeout as timeout_err:
            print(f"Timeout error occurred: {timeout_err}")
            raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="Request to X API timed out.")
        except requests.exceptions.RequestException as req_err:
            print(f"An error occurred during the request: {req_err}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unknown error occurred: {req_err}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")

    return all_feeds



credentials = service_account.Credentials.from_service_account_file(glob.env.get("VERTEX_CREDENTIALS_FILE"))

# Initialize Pub/Sub client with credentials
publisher = pubsub_v1.PublisherClient(credentials=credentials)
topic_path = publisher.topic_path(glob.env.get("VERTEX_PROJECT_ID"), glob.env.get("VERTEX_TOPIC_ID"))


def load_jsons(file_path=glob.env.get("VERTEX_DATA_FILE")):
    with open(file_path, "r") as f:
        return json.load(f)  
    

def publish_x_feeds():
    try: 
        data_list = load_jsons()
        if not data_list:
            return {"error": "No JSON data found."}
        
        random_json = random.choice(data_list)
        message_bytes = json.dumps(random_json).encode("utf-8")

        future = publisher.publish(topic_path, message_bytes)
        future.result()
    except Exception as e:
        raise {"error": str(e)}
