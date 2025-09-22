import os
from core.redis_client import get_redis_data
from dotenv import load_dotenv
from .langchain_suggestion import rag_for_suggestion
import asyncio
import json
import traceback
import redis.asyncio as redis
import time
from redis.exceptions import ResponseError, ConnectionError, TimeoutError

load_dotenv('/Users/macbook/Desktop/BangA_DSC2025/.env')
QUEUE_PASSIVE_SUGGESTION = os.getenv("QUEUE_PASSIVE_SUGGESTION", "queue_passive_suggestion")

async def process_job(job_data: dict):
    await rag_for_suggestion(job_data)

PING_INTERVAL = 1800  # 30 phút ping Redis 1 lần
async def worker_loop():
    global redis_data
    redis_data = await get_redis_data()
    print("[Suggestion_Worker] Started worker loop...")
    last_ping = time.time()
    while True:
        if time.time() - last_ping > PING_INTERVAL:
            try:
                pong = await redis_data.ping()
                if pong is True:
                    print("[Worker] Redis ping OK")
                else:
                    print("[Worker] Redis ping failed → reconnecting")
                    redis_data = await get_redis_data()
            except Exception as e:
                print(f"[Worker] Redis ping error: {e} → reconnecting")
                redis_data = await get_redis_data()
            last_ping = time.time()

        try:
            if redis_data is None:
                redis_data = await get_redis_data()

            job_json = await redis_data.brpop(QUEUE_PASSIVE_SUGGESTION, timeout=5)

        except ResponseError as e:
            print(f"[Worker] BRPOP was force-unblocked, retrying... {e}")
            await asyncio.sleep(0.5)
            continue

        except (ConnectionError, TimeoutError) as e:
            print(f"[Worker] Redis connection lost: {e}. Reconnecting...")
            redis_data = None  # force reconnect
            traceback.print_exc()
            await asyncio.sleep(1)
            continue

        except Exception as e:
            print(f"[Worker] Unexpected error during BRPOP: {e}")
            traceback.print_exc()
            await asyncio.sleep(1)
            continue

        if job_json is None:
            continue

        _, job_str = job_json
        job_data = json.loads(job_str)

        try:
            await process_job(job_data) 
        except Exception as e:
            print(f"[Suggestion_Worker] Error processing job {job_data.get('job_id')}: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(worker_loop())
    except KeyboardInterrupt:
        print("\n[Suggestion_Worker] Stopped by user (Ctrl+C)")


# python -m passive_suggestion.suggest_worker 


