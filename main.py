# Description: Main script for running the bot and updating the dataset at regular intervals.
import subprocess
import time
import sched
import threading
import logging
from db_manage.db_manager import db_manager
from chain_observer.utils.check_thread_status import check_update_thread_status
from chain_observer.utils.sentry import init_sentry

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_script(script_name):
    """Runs a specified Python script."""
    try:
        subprocess.run(['python', script_name], check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"Error executing script {script_name}: {e}")

def schedule_task(scheduler, task, interval, *args):
    """Schedules a task to run at regular intervals."""
    threading.Thread(target=task, args=args).start()
    scheduler.enter(interval, 1, schedule_task, (scheduler, task, interval) + args)

def update_coldkeys():
    """Executes find_validator_coldkey and find_owner_coldkey in sequence."""
    if check_update_thread_status() == 'not running':
        db_manager.update_whole_owner_coldkeys()
    db_manager.update_whole_validator_coldkeys()

if __name__ == "__main__":
    
    init_sentry()
    
    bot_interval = 12  # Interval in seconds for running the bot
    update_dataset_interval = 86400  # Interval in seconds for updating the dataset (1 day)
    initial_delay = 86400  # Delay in seconds before starting the dataset update (1 day)

    scheduler = sched.scheduler(time.time, time.sleep)
    scheduler.enter(0, 1, schedule_task, (scheduler, run_script, bot_interval, 'run.py'))
    scheduler.enter(initial_delay, 1, schedule_task, (scheduler, update_coldkeys, update_dataset_interval))
    
    try:
        logging.info("Starting the scheduler.")
        scheduler.run()
    except KeyboardInterrupt:
        logging.info("Scheduler terminated by user.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
