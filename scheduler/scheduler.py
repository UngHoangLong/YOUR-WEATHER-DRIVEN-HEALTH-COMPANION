import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import sys
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from .scheduler_suggestion import push_job_passive_suggestion
from .scheduler_push_job_collect_data import push_jobs_collect_data

# Múi giờ Việt Nam
VIETNAM_TIMEZONE = ZoneInfo("Asia/Ho_Chi_Minh")

async def run_push_job_passive_suggestion():
    """
    Hàm wrapper để lấy ngày, tháng, năm hiện tại theo múi giờ Việt Nam
    và truyền vào hàm lập lịch.
    """
    now = datetime.now(VIETNAM_TIMEZONE)
    day_now = now.day
    month_now = now.month
    year_now = now.year
    # Gọi hàm push_job_passive_suggestion với các tham số đã lấy được
    await push_job_passive_suggestion(day_now, month_now, year_now)

async def main():
    scheduler = AsyncIOScheduler(timezone=VIETNAM_TIMEZONE)
    scheduler.add_job(push_jobs_collect_data, "cron", hour=0, minute=1)
    scheduler.add_job(run_push_job_passive_suggestion, "cron", hour=0, minute=30)
    scheduler.start()
    print("[Scheduler] Push job scheduled for 0h01 (collect data) and 0h30 (suggestion) daily.")

    try:
        # Giữ scheduler chạy mãi.
        # asyncio.Future() là một cách để tạo một đối tượng chờ không bao giờ hoàn thành,
        # giúp giữ event loop chạy.
        # Đây là cách chính thống để giữ một chương trình asyncio chạy vô hạn.
        await asyncio.Future()
    except (KeyboardInterrupt, SystemExit):
        # Cho phép chương trình dừng lại khi người dùng nhấn Ctrl+C
        print("[Scheduler] Stopped by user (Ctrl+C)")
    finally:
        scheduler.shutdown()

if __name__ == "__main__":
    asyncio.run(main())


# python -m scheduler.scheduler