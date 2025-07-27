# chron.py
import requests
import time 
import sys
import json
import asyncio 
from utilities.help_func import LOGS


# Make the function asynchronous
async def hit_api_repeatedly(api_url, interval_seconds=15):
    # Use await for all aiologger calls
    await LOGS.alog_info(f"Starting API calls to {api_url} every {interval_seconds} seconds.")
    # For console output, you can still use print directly
    print("Press Ctrl+C to stop the script.")

    try:
        while True:
            try:
                # requests.get is a synchronous call, so no await here
                response = requests.post(api_url)
                response.raise_for_status()
                await LOGS.alog_info(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] API call successful. Status Code: {response.status_code}")
            except requests.exceptions.RequestException as e:
                await LOGS.alog_error(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Error hitting API: {e}")
            except json.JSONDecodeError:
                await LOGS.alog_error(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Error decoding JSON response. Response text: {response.text}")
            except Exception as e: # Catch any other unexpected exceptions
                await LOGS.alog_error(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] An unexpected error in loop: {e}")


            # Use asyncio.sleep for non-blocking sleep
            await asyncio.sleep(interval_seconds)

    except KeyboardInterrupt:
        await LOGS.alog_error("\nAPI polling interrupted by user (Ctrl+C). Exiting.")
        print("\nAPI polling interrupted by user (Ctrl+C). Exiting.") # Also print to console
    except Exception as e:
        await LOGS.alog_error(f"\nAn unexpected error occurred in main loop: {e}")
    finally:
        # Crucial: Ensure the logger is shut down to flush all pending logs
        await LOGS.close()
        sys.exit(0) # Exit the program cleanly

if __name__ == "__main__":
    
    target_api_url = "http://127.0.0.1:8000/x/publish-random-feeds"

    # Run the asynchronous main function using asyncio.run()
    asyncio.run(hit_api_repeatedly(target_api_url, 15))