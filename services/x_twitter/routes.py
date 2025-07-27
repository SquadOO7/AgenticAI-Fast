from fastapi import HTTPException, APIRouter
from datetime import datetime, timedelta, timezone
import json
import os
from utilities.help_func import LOGS
from services.x_twitter.operation import get_user_id, get_user_tweets, fetch_bengaluru_feeds_from_x, publish_x_feeds

router = APIRouter()


@router.get("/fetch-handle-feeds")
async def fetch_feeds(handle_name: str):
    tweets = []

    if not handle_name:
        raise HTTPException(status_code=500, detail= "handle name not found")
    
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days=7)

    start_time_str = start_time.isoformat(timespec="seconds").replace("+00:00", "Z")
    end_time_str = end_time.isoformat(timespec="seconds").replace("+00:00", "Z")

    user_id = await get_user_id(handle_name)
    tweets = await get_user_tweets(user_id, start_time_str, end_time_str)

    geo = "12.9611,77.6387" 
    tweets.extend([
        {
            "text": tweet["text"],
            "image_url": [],
            "video_url": [],
            "audio_url": [],
            "geolocation": geo
        }
        for tweet in tweets
    ])

    # Load existing tweets if the file exists
    if os.path.exists("bangalore_feeds.json"):
        with open("bangalore_feeds.json", "r", encoding="utf-8") as f:
            existing_tweets = json.load(f)
    else:
        existing_tweets = []

    # Append new tweets
    existing_tweets.extend(tweets)

    # Save updated tweets back to the file
    with open("bangalore_feeds.json", "w", encoding="utf-8") as f:
        json.dump(existing_tweets, f, indent=2, ensure_ascii=False)

    await LOGS.alog_info({"message": f"Fetched {len(tweets)} tweets from {handle_name} accounts", "saved_to": "bangalore_feeds.json"})

    return {"message": f"Fetched {len(tweets)} tweets from {handle_name} accounts", "saved_to": "bangalore_feeds.json"}


@router.get("/bengaluru-feeds", summary="Get Bengaluru City Feeds from X", response_description="A list of categorized tweets for Bengaluru.")
async def get_bengaluru_city_feeds():
    feeds = fetch_bengaluru_feeds_from_x()
    return {"message": "Successfully fetched Bengaluru feeds", "data": feeds, "count": len(feeds)}



@router.post("/publish-random-feeds")
async def publish_json():
    try:
        publish_x_feeds()
    except Exception as e:
        raise {"error": str(e)}