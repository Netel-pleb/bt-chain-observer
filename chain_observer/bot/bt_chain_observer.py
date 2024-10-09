import pytz
from datetime import datetime
from substrateinterface.base import SubstrateInterface
import bittensor as bt
from dotenv import load_dotenv
import os
import logging
from db_manage.db_manager import db_manager
from chain_observer.bot.generate_reports import generate_report, generate_vote_report, generate_dissolved_netword

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

class BtChainObserver:
    """
    Observe bittensor blockchain extrisics and events for schedule_swap_coldkey, schedule_dissolve_network, vote, coldkey_swapped and network_dissolved.
    """
    def __init__(self):
        
        self.substrate = self.setup_substrate_interface()

    def setup_substrate_interface(self):
        """
        Initializes and returns a SubstrateInterface object configured to connect to a specified WebSocket URL.
        This interface will be used to interact with the blockchain.
        """
        try:
            SUBTENSOR_ENDPOINT = os.getenv('SUBTENSOR_ENDPOINT')
            if not SUBTENSOR_ENDPOINT:
                logging.error("SUBTENSOR_ENDPOINT is not set in environment variables.")
                return None
            return SubstrateInterface(
                url=SUBTENSOR_ENDPOINT,
                ss58_format=42,
                use_remote_preset=True,
            )
        except Exception as e:
            logging.exception("Failed to initialize SubstrateInterface. Please check the WebSocket URL and network connection.")
            return None

    def get_block_data(self, block_number):
        """
        Retrieves block data and associated events from the blockchain for a given block number.
        """
        try:
            block_hash = self.substrate.get_block_hash(block_id=block_number)
            block = self.substrate.get_block(block_hash=block_hash)
            events = self.substrate.get_events(block_hash=block_hash)
            return block, events
        except Exception as e:
            logging.exception(f"Failed to retrieve block data for block number {block_number}. Please verify the block number and network status.")
            return None, None

    def extract_block_timestamp_from_extrinsics(self, extrinsics):
        """
        Extracts the timestamp from a list of extrinsics by identifying the 'set' function call within the 'Timestamp' module.
        Returns the timestamp formatted as 'YYYY-MM-DD HH:MM:SS (UTC±X)'.
        """
        try:
            for extrinsic in extrinsics:
                extrinsic_value = getattr(extrinsic, 'value', None)
                if extrinsic_value and 'call' in extrinsic_value:
                    call = extrinsic_value['call']
                    if call['call_function'] == 'set' and call['call_module'] == 'Timestamp':
                        timestamp = call['call_args'][0]['value'] / 1000
                        dt_utc = datetime.fromtimestamp(timestamp, tz=pytz.UTC)
                        utc_offset = dt_utc.strftime('%z')
                        formatted_offset = f'UTC{utc_offset[:3]}:{utc_offset[3:]}'
                        return dt_utc.strftime(f'%Y-%m-%d %H:%M:%S ({formatted_offset})')
            return None
        except Exception as e:
            logging.exception("Error extracting timestamp from extrinsics.")
            return None

    def find_extrinsic_indices(self, extrinsics, schedule_swap_coldkey_func, schedule_dissolve_subnet_func, vote_func, module_name):
        """
        Finds indices of specific extrinsic calls in the list of extrinsics.
        Returns a tuple of indices for each function if found, otherwise -1 for each.
        """
        try:
            schedule_swap_coldkey_idx, schedule_dissolve_network_idx, vote_idx = -1, -1, -1
            for idx, extrinsic in enumerate(extrinsics):
                extrinsic_value = getattr(extrinsic, 'value', None)
                if extrinsic_value and 'call' in extrinsic_value:
                    call = extrinsic_value['call']
                    if call['call_module'] == module_name:
                        if call['call_function'] == schedule_swap_coldkey_func:
                            schedule_swap_coldkey_idx = idx
                        elif call['call_function'] == schedule_dissolve_subnet_func:
                            schedule_dissolve_network_idx = idx
                        elif call['call_function'] == vote_func:
                            vote_idx = idx
            return schedule_swap_coldkey_idx, schedule_dissolve_network_idx, vote_idx
        except Exception as e:
            logging.exception("Error checking extrinsic calls.")
            return -1, -1, -1

    def extract_schedule_coldkey_swap_details(self, extrinsic_events):
        """
        Extracts details of schedule coldkey swap events from extrinsic events.
        Returns a tuple of old_coldkey, new_coldkey, and execution_block if found.
        """
        try:
            for event in extrinsic_events:
                event_value = getattr(event, 'value', None)
                if event_value and event_value['event_id'] == 'ColdkeySwapScheduled':
                    old_coldkey = event_value['attributes']['old_coldkey']
                    new_coldkey = event_value['attributes']['new_coldkey']
                    execution_block = event_value['attributes']['execution_block']
                    return old_coldkey, new_coldkey, execution_block
            return None
        except Exception as e:
            logging.exception("Error extracting schedule coldkey swap details.")
            return None

    def extract_schedule_network_dissolve_details(self, extrinsic_events):
        """
        Extracts details of schdule network dissolve events from extrinsic events.
        Returns a tuple of netuid, owner_coldkey, and execution_block if found.
        """
        try:
            for event in extrinsic_events:
                event_value = getattr(event, 'value', None)
                if event_value and event_value['event_id'] == 'DissolveNetworkScheduled':
                    netuid = event_value['attributes']['netuid']
                    owner_coldkey = event_value['attributes']['account']
                    execution_block = event_value['attributes']['execution_block']
                    return netuid, owner_coldkey, execution_block
            return None
        except Exception as e:
            logging.exception("Error extracting schedule network dissolve details.")
            return None

    def collect_extrinsic_events_and_status(self, events, idx):
        """
        Collects events related to a specific extrinsic and checks if it was successful.
        Returns a list of events and a boolean indicating success.
        """
        try:
            extrinsic_events = []
            extrinsic_success = False
            for event in events:
                event_value = getattr(event, 'value', None)
                if event_value and event_value.get('extrinsic_idx') == idx:
                    extrinsic_events.append(event)
                    if event_value['event_id'] == 'ExtrinsicSuccess':
                        extrinsic_success = True
            return extrinsic_events, extrinsic_success
        except Exception as e:
            logging.exception("Error collecting extrinsic events and status.")
            return [], False

    def extract_vote_details(self, extrinsic):
        """
        Extracts specific parameters from the vote extrinsic data.

        Parameters:
        extrinsic (GenericExtrinsic): The extrinsic data.

        Returns:
        tuple: A tuple containing the extracted parameters: hotkey, proposal, approve, and index.
        """
        try:
            hotkey = proposal = approve = index = None
            call_args = extrinsic.value['call']['call_args']

            for arg in call_args:
                if arg['name'] == 'hotkey':
                    hotkey = arg['value']
                elif arg['name'] == 'proposal':
                    proposal = arg['value']
                elif arg['name'] == 'approve':
                    approve = arg['value']
                elif arg['name'] == 'index':
                    index = arg['value']

            return hotkey, proposal, approve, index
        except Exception as e:
            logging.exception("Error extracting vote details.")
            return None, None, None, None

    def find_swapped_coldeky_and_dissolved_network(self, events, swapped_event, dissolved_event):
        """
        Checks for specific swap and dissolve events in the list of events.

        Parameters:
        events (list): List of event objects.
        swap_event (str): The event name of the swapped coldkey event.
        dissolve_event (str): The event name of the dissolved network event.

        Returns:
        tuple: A tuple containing swapped old coldkey, swapped new coldkey, and dissolved network UID.
        """
        try:
            swapped_old_coldkey = swapped_new_coldkey = dissolved_network_uid = None
            for event in events:
                event_value = getattr(event, 'value', None)
                if event_value and event_value.get('event_id') == swapped_event:
                    swapped_old_coldkey = event_value['attributes'].get('old_coldkey')
                    swapped_new_coldkey = event_value['attributes'].get('new_coldkey')
                elif event_value and event_value.get('event_id') == dissolved_event:
                    dissolved_network_uid = event_value['attributes']

            return swapped_old_coldkey, swapped_new_coldkey, dissolved_network_uid
        except Exception as e:
            logging.exception("Error finding swap and dissolve events.")
            return None, None, None

    def extract_failed_schedule_swap_coldkey_details(self, extrinsic_events):
        """
        Extracts details of failed schedule coldkey swap events from extrinsic events.
        Returns a coldkey of executor
        """
        try:
            for event in extrinsic_events:
                event_value = getattr(event, 'value', None)
                if event_value and event_value['event_id'] == 'Withdraw':
                    old_coldkey = event_value['attributes']['who']
                    return old_coldkey
            return None
        except Exception as e:
            logging.exception("Error extracting failed schedule coldkey swap details.")


    def process_schedule_swap_coldkey(self, extrinsics, events, schedule_swap_coldkey_idx, current_block_number):
        """
        Processes scheduled coldkey swap extrinsics and generates a report.

        Parameters:
        - extrinsics (list): List of extrinsics.
        - events (list): List of events.
        - schedule_swap_coldkey_idx (int): Index of the scheduled swap coldkey extrinsic.
        - current_block_number (int): Current block number.

        Returns:
        - str: The generated report.
        """        
        time_stamp = self.extract_block_timestamp_from_extrinsics(extrinsics)
        extrinsic_events, extrinsic_success = self.collect_extrinsic_events_and_status(events, schedule_swap_coldkey_idx)
        old_coldkey, new_coldkey, execution_block = self.extract_schedule_coldkey_swap_details(extrinsic_events) if extrinsic_success else (None, None, None)
        if extrinsic_success == False:
            old_coldkey = self.extract_failed_schedule_swap_coldkey_details(extrinsic_events)
        validator_name, validator_hotkey, check_validator = db_manager.get_validator_name(old_coldkey)
        link = f"https://taostats.io/validators/{validator_hotkey}"
        original_coldkey = old_coldkey
        if check_validator:
            if validator_name:
                old_coldkey = old_coldkey + f"\n(Validator : [{validator_name}]({link}))"
            else: 
                old_coldkey = old_coldkey + f"\n(Validator : [no name]({link}))"
        netuid = db_manager.get_owner_netuid(original_coldkey)
        if netuid:
            link = f"https://taostats.io/subnets/{netuid}/metagraph"
            old_coldkey = f"{old_coldkey}\n([subnet{netuid} owner]({link}))"
        
        details = {
            "current_block_number": current_block_number,
            "identifier": old_coldkey,
            "new_coldkey": new_coldkey,
            "execution_block": execution_block
        }
        schedule_swap_coldkey_report = generate_report("📅 __ NEW SCHEDULE_SWAP_COLDKEY DETECTED __ 📅", extrinsic_success, details, time_stamp)     
        return schedule_swap_coldkey_report
        
    def process_schedule_dissolve_subnet(self, extrinsics, events, schedule_dissolve_network_idx, current_block_number):  
        """
        Processes scheduled network dissolve extrinsics and generates a report.

        Parameters:
        - extrinsics (list): List of extrinsics.
        - events (list): List of events.
        - schedule_dissolve_network_idx (int): Index of the scheduled dissolve network extrinsic.
        - current_block_number (int): Current block number.

        Returns:
        - str: The generated report.
        """        
        time_stamp = self.extract_block_timestamp_from_extrinsics(extrinsics)
        extrinsic_events, extrinsic_success = self.collect_extrinsic_events_and_status(events, schedule_dissolve_network_idx)
        netuid, owner_coldkey, execution_block = self.extract_schedule_network_dissolve_details(extrinsic_events) if extrinsic_success else (None, None, None)
        link = f"https://taostats.io/subnets/{netuid}/metagraph"
        netuid = f"[{netuid}]({link})"

        details = {
            "current_block_number": current_block_number,
            "identifier": owner_coldkey,
            "owner_coldkey": owner_coldkey,
            "execution_block": execution_block
        }
        schedule_dissolve_subnet_report = generate_report("⏳ __SCHEDULE_NETWORK_DISSOLVE DETECTED__ ⏳", extrinsic_success, details, time_stamp) 
        return schedule_dissolve_subnet_report
        
    def process_vote(self, extrinsics, events, vote_idx, current_block_number):
        """
        Processes vote extrinsics and generates a report.

        Parameters:
        - extrinsics (list): List of extrinsics.
        - events (list): List of events.
        - vote_idx (int): Index of the vote extrinsic.
        - current_block_number (int): Current block number.

        Returns:
        - str: The generated report.
        """
        time_stamp = self.extract_block_timestamp_from_extrinsics(extrinsics)
        extrinsic_events, extrinsic_success = self.collect_extrinsic_events_and_status(events, vote_idx)
        hotkey, proposal, approve, index = self.extract_vote_details(extrinsics[vote_idx])
        validator_name, validator_coldkey, check_validator = db_manager.get_validator_name(None, hotkey)
        link = f"https://taostats.io/validators/{hotkey}"
        if check_validator:
            if validator_name:
                hotkey = hotkey + f"\n([Validator : {validator_name}]({link}))"
            else: 
                hotkey = hotkey + f"\n([Validator : no name]({link}))"
        details = {
            "current_block_number": current_block_number,
            "hotkey": hotkey,
            "proposal": proposal,
            "index": index,
            "approve": approve,
        }
        vote_report = generate_vote_report("🗳️ __ NEW VOTE DETECTED __ 🗳️", extrinsic_success, details, time_stamp)    
        return vote_report
        
    def process_swapped_coldkey(self, extrinsics, swapped_old_coldkey, swapped_new_coldkey, current_block_number):
        """
        Processes coldkey swap events and generates a report.

        Parameters:
        - extrinsics (list): List of extrinsics.
        - swapped_old_coldkey (str): The old coldkey that was swapped.
        - swapped_new_coldkey (str): The new coldkey that was swapped to.
        - current_block_number (int): Current block number.

        Returns:
        - str: The generated report.
        """
        time_stamp = self.extract_block_timestamp_from_extrinsics(extrinsics)
        validator_name, validator_hotkey, check_validator = db_manager.get_validator_name(swapped_old_coldkey)
        link = f"https://taostats.io/validators/{validator_hotkey}"
        original_coldkey = swapped_old_coldkey
        if check_validator:  
            db_manager.update_validator_coldkey(swapped_old_coldkey, swapped_new_coldkey)
            if validator_name:
                swapped_old_coldkey = swapped_old_coldkey + f"\n(Validator : [{validator_name}]({link}))"
            else: 
                swapped_old_coldkey = swapped_old_coldkey + f"\n(Validator : [no name]({link}))" 
        netuid = db_manager.get_owner_netuid(original_coldkey)
        if netuid:
            db_manager.update_owner_coldkey(netuid, swapped_new_coldkey)
            link = f"https://taostats.io/subnets/{netuid}/metagraph"
            swapped_old_coldkey = f"{swapped_old_coldkey}\n([subnet{netuid} owner]({link}))"       
        details = {
            "current_block_number": current_block_number,
            "old_coldkey": swapped_old_coldkey,
            "new_coldkey": swapped_new_coldkey,
        }
        swapped_coldkey_report = generate_report(" __😍 COLDKEY SWAPPED 😍__ ", True, details, time_stamp)   
        return swapped_coldkey_report     
    
    def process_dissolved_network(self, extrinsics, current_block_number, dissolved_network_uid):
        """
        Processes network dissolve events and generates a report.

        Parameters:
        - extrinsics (list): List of extrinsics.
        - current_block_number (int): Current block number.
        - dissolved_network_uid (str): The UID of the dissolved network.

        Returns:
        - tuple: The generated report and a flag indicating if the owner table should be updated.
        """
        time_stamp = self.extract_block_timestamp_from_extrinsics(extrinsics)
        details = {
            "current_block_number": current_block_number,
            "netuid": dissolved_network_uid,
        }
        dissloved_subnet_resport = generate_dissolved_netword("😯 __ NETWORK DESSOLVED __ 😯", details, time_stamp)
        should_update_owner_table = True     
        return dissloved_subnet_resport, should_update_owner_table   
    
    def bt_block_observer(self):
        """
        Observes the current block for scheduled coldkey swaps and network dissolves, generating reports for each.
        """
        
        current_block_number = bt.subtensor().get_current_block()
        
        db_manager.verify_update_block_number(current_block_number)
        
        block, events = self.get_block_data(current_block_number)
        schedule_swap_coldkey_report, schedule_dissolve_subnet_report, vote_report, dissloved_subnet_resport, swapped_coldkey_report = None, None, None, None, None
        should_update_owner_table = False
        
        # Check for extrinsics related to scheduled coldkey swap, schedule network dissolve and vote
        schedule_swap_coldkey_func = 'schedule_swap_coldkey'
        schedule_dissolve_subnet_func = 'schedule_dissolve_network'
        vote_func = 'vote'
        call_module = 'SubtensorModule'
        schedule_swap_coldkey_idx, schedule_dissolve_network_idx, vote_idx = self.find_extrinsic_indices(block['extrinsics'], schedule_swap_coldkey_func, schedule_dissolve_subnet_func, vote_func, call_module)
        
        # Check for events related to coldkey swapped and network dissolved
        swapped_event = 'ColdkeySwapped'
        dissolved_event = 'NetworkRemoved'
        swapped_old_coldkey, swapped_new_coldkey, dissolved_network_uid = self.find_swapped_coldeky_and_dissolved_network(events, swapped_event, dissolved_event)
        
        # Check and process scheduled coldkey swap
        if schedule_swap_coldkey_idx >= 0:
            schedule_swap_coldkey_report = self.process_schedule_swap_coldkey(block['extrinsics'], events, schedule_swap_coldkey_idx, current_block_number)

        # Check and process scheduled network dissolve
        if schedule_dissolve_network_idx >= 0:
            schedule_dissolve_subnet_report = self.process_schedule_dissolve_subnet(block['extrinsics'], events, schedule_dissolve_network_idx, current_block_number)

        # Check and process vote
        if vote_idx >= 0:
            vote_report = self.process_vote(block['extrinsics'], events, vote_idx, current_block_number)
        # Check and processr coldkey swapped
        if swapped_old_coldkey:
            swapped_coldkey_report = self.process_swapped_coldkey(block['extrinsics'], swapped_old_coldkey, swapped_new_coldkey, current_block_number)    

        #Check and process dissolved network
        if dissolved_network_uid:
            dissloved_subnet_resport, should_update_owner_table = self.process_dissolved_network(block['extrinsics'], current_block_number, dissolved_network_uid)


        return schedule_swap_coldkey_report, schedule_dissolve_subnet_report, vote_report, dissloved_subnet_resport, swapped_coldkey_report, should_update_owner_table
