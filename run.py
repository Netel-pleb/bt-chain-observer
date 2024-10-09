import os
import time
from datetime import datetime
import threading
import logging
from dotenv import load_dotenv
from chain_observer.bot.discord_report import post_to_discord
from chain_observer.bot.bt_chain_observer import BtChainObserver
from db_manage.db_manager import db_manager
from chain_observer.utils.check_thread_status import check_update_thread_status

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

COLDKEY_SWAP_DISCORD_WEBHOOK_URL = os.getenv('COLDKEY_SWAP_DISCORD_WEBHOOK_URL')
DISSOLVE_NETWORK_DISCORD_WEBHOOK_URL = os.getenv('DISSOLVE_NETWORK_DISCORD_WEBHOOK_URL')
chain_observer = BtChainObserver()

def run_update_owner_coldkey_function():
    """Runs the find_owner_coldkey function in a new thread."""
    try:
        with open('config/thread_status.status', 'w') as f:
            f.write('running')
        db_manager.update_whole_owner_coldkeys()
    except Exception as e:
        logging.error(f"Error in updating owner coldkey: {e}")
    finally:
        with open('config/thread_status.status', 'w') as f:
            f.write('not running')

def run_bot():
    """Process and send reports to Discord."""
    try:
        (report_swap_coldkey, report_dissolve_network, report_vote, 
         dissolved_subnet_report, swapped_coldkey_report, 
         should_update_owner_table) = chain_observer.bt_block_observer()
        
        if should_update_owner_table:
            thread_status = check_update_thread_status()
            if thread_status == 'not running':
                update_owner_thread = threading.Thread(target=run_update_owner_coldkey_function)
                update_owner_thread.start()
            else:
                logging.info("Update owner coldkey function is already running.")

        reports = [
            (report_swap_coldkey, COLDKEY_SWAP_DISCORD_WEBHOOK_URL),
            (report_dissolve_network, DISSOLVE_NETWORK_DISCORD_WEBHOOK_URL),
            (dissolved_subnet_report, DISSOLVE_NETWORK_DISCORD_WEBHOOK_URL),
            (report_vote, COLDKEY_SWAP_DISCORD_WEBHOOK_URL),
            (swapped_coldkey_report, COLDKEY_SWAP_DISCORD_WEBHOOK_URL),
        ]
        
        # Post reports to Discord only if they have values
        for report, webhook_url in reports:
            if report:
                post_to_discord(report, webhook_url)
    except Exception as e:
        logging.error(f"Error during running bot: {e}")

def run():
    """Main function to run the bot process."""
    time_now = datetime.now()
    start_time = time.time()
    logging.info(f"Bot process started at {time_now.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}.")
    
    run_bot()
    
    end_time = time.time()
    logging.info(f"Process completed in {end_time - start_time:.3f} seconds.")

if __name__ == "__main__":
    run()
