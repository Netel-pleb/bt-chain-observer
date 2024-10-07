# Description: Main script for running the bot and updating the dataset at regular intervals.
import subprocess
import time
import sched
import threading
from observing.utils.get_coldkeys import find_owner_coldkey, find_validator_coldkey
import os
import sentry_sdk
from dotenv import load_dotenv

def init_sentry(): 
    """Initialize Sentry"""
    load_dotenv()
    SENTRY_DSN = os.getenv('SENTRY_DSN')
    
    sentry_sdk.init(
        dsn=SENTRY_DSN,  
        traces_sample_rate=1.0
    )

def run_bot():
    """Runs a specified script."""
    subprocess.run(['python', 'run.py'])  # Replace 'run.py' with the actual filename if different


def schedule_bot(scheduler, interval):
    """Schedules the bot to run at regular intervals."""

    threading.Thread(target=run_bot).start()
    scheduler.enter(interval, 1, schedule_bot, (scheduler, interval))


def update_coldkeys():
    """Runs find_validator_coldkey and find_owner_coldkey in sequence."""

    status = check_thread_status()
    if status == 'not running':
        find_owner_coldkey()
    find_validator_coldkey()


def schedule_update_dataset(scheduler, interval):
    """Schedules the dataset to update at regular intervals."""

    threading.Thread(target=update_coldkeys).start()
    scheduler.enter(interval, 1, schedule_update_dataset, (scheduler, interval))


def check_thread_status():
    try:
        with open('thread_status.status', 'r') as f:
            status = f.read().strip()
            return status
    except FileNotFoundError:
        return 'not running'

if __name__ == "__main__":
    init_sentry()
    
    bot_interval = 12  # Interval in seconds for running the bot
    update_dataset_interval = 86400  # Interval in seconds for updating the dataset (1 day)
    initial_delay = 86400  # Delay in seconds before starting the dataset update (1 day)

    scheduler = sched.scheduler(time.time, time.sleep)
    scheduler.enter(0, 1, schedule_bot, (scheduler, bot_interval))
    scheduler.enter(initial_delay, 1, schedule_update_dataset, (scheduler, update_dataset_interval))
    scheduler.run()
