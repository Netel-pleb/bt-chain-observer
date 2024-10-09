import sentry_sdk
import sqlite3
from dotenv import load_dotenv
import os
import requests
import time
import logging
from chain_observer.utils.owner_coldkeys import get_subnet_owner_coldkeys

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
DB_PATH = 'database/db.sqlite3'

class DBManager:
    
    def __init__(self):
        """
        initialize the database connection with conn and cursor and also get the TAOSTATS_API_KEY from the environment variable.
        """       
        conn = sqlite3.connect(DB_PATH)      
        if not conn:
            raise Exception("Database connection failed.")        
        self.TAOSTATS_API_KEY = os.getenv("TAOSTATS_API_KEY")
        
    def create_table_if_not_exist(self, table_name):
        """
        create table if not exist
        """          
        conn = sqlite3.connect(DB_PATH)   
        cursor = conn.cursor()
        
        sql = f'''
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            current_block_number TEXT
        )
        '''
        cursor.execute(sql)
        
    def get_validator_name(self, coldkey, hotkey=None):
        """
        Retrieves the name and hot_key of a validator based on their coldkey.
        
        Parameters:
        coldkey (str): The coldkey of the validator.
        
        Returns:
        tuple: (name, hot_key, status) where name and hot_key are the values of the validator if found,
            otherwise None, and status is 1 if the coldkey exists, otherwise 0.
        """        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        try:
            if coldkey:
                cursor.execute('SELECT name, hot_key FROM validators WHERE cold_key = ?', (coldkey,))
                result = cursor.fetchone()
            else:
                cursor.execute('SELECT name, cold_key FROM validators WHERE hot_key = ?', (hotkey,))
                result = cursor.fetchone()
            if result:
                return result[0], result[1], 1
            else:
                return None, None, 0
        except sqlite3.Error as e:
            logging.exception(f"Database error in get_validator_name : {e}")
            return None, None, 0

    def get_owner_netuid(self, coldkey):
        """
        Retrieves the name of the owner based on their coldkey.
        
        Parameters:
        coldkey (str): The coldkey of the owner.
        
        Returns:
        tuple: (name, status) where name is the value of the owner if found, otherwise None, and status is 1 if the coldkey exists, otherwise 0.
        """
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('SELECT net_uid FROM owners WHERE owner_coldkey = ?', (coldkey,))
            result = cursor.fetchone()
            if result:
                return result[0]
            else:
                return None
        except sqlite3.Error as e:
            logging.exception(f"Database error in get_owner_name : {e}")
            return None
    
    def verify_update_block_number(self, current_block_number):   
        try:            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            self.create_table_if_not_exist("block_number_table")
            
            cursor.execute('SELECT current_block_number FROM block_number_table LIMIT 1')
            result = cursor.fetchone()
            
            if result:
                previous_block_number = int(result[0])
                logging.info(f"Previous block number: {previous_block_number}, Current block number: {current_block_number}")
                if current_block_number - previous_block_number != 1:
                    raise ValueError(f"Block number difference is not 1, {current_block_number} - {previous_block_number}.")
            
            cursor.execute('DROP TABLE IF EXISTS block_number_table')
            
            self.create_table_if_not_exist('block_number_table')
            
            cursor.execute('''
            INSERT INTO block_number_table (current_block_number)
            VALUES (?)
            ''', (current_block_number,))
            conn.commit()
        except ValueError as ve:
            sentry_sdk.capture_exception(ve)
            logging.error(f"ValueError in check_update_block_number: {ve}")
            try:
                cursor.execute('DROP TABLE IF EXISTS block_number_table')
                self.create_table_if_not_exist('block_number_table')
                cursor.execute('''
                INSERT INTO block_number_table (current_block_number)
                VALUES (?)
                ''', (current_block_number,))
                conn.commit()
            except sqlite3.Error as e:
                logging.error(f"Error in updating block number after ValueError: {e}")
        except sqlite3.Error as e:
            logging.error(f"Error in verify_update_block_number: {e}")

    def update_validator_coldkey(self, old_coldkey, new_coldkey):
        """
        Updates the coldkey of a validator in the database.
        
        Parameters:
        old_coldkey (str): The old coldkey of the validator.
        new_coldkey (str): The new coldkey of the validator.
        """
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('UPDATE validators SET cold_key = ? WHERE cold_key = ?', (new_coldkey, old_coldkey))
            conn.commit()
            logging.info("Coldkey updated successfully.")
        except sqlite3.Error as e:
            logging.error(f"Database error: {e}")

    def update_owner_coldkey(self, net_uid, new_coldkey):
        """
        Updates the coldkey of an owner in the database.
        
        Parameters:
        net_uid (str): The net_uid of the owner.
        new_coldkey (str): The new coldkey of the owner.
        """
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('UPDATE owners SET owner_coldkey = ? WHERE net_uid = ?', (new_coldkey, net_uid))
            conn.commit()
            logging.info("Owner coldkey updated successfully.")
        except sqlite3.Error as e:
            logging.error(f"Database error: {e}")
        logging.exception("Owner coldkey data has updated with new coldkey.(one element)")
    
    def fetch_all_validators(self, url, headers):
        """
        Fetches all validators using pagination.
        
        Args:
            url (str): The API endpoint URL.
            headers (dict): The headers to include in the API request.
        
        Returns:
            list: A list of all validators.
        """
        
        validators = []
        page = 1
        while True:
            params = {
                "order": "amount:desc",
                "page": page
            }
            response = requests.get(url, headers=headers, params=params)
            data = response.json()
            if not data['validators']:
                break
            validators.extend(data['validators'])
            page += 1
        return validators

    def update_whole_owner_coldkeys(self):
        """
        Fetches owner coldkeys and net_uids from the API and saves them to the SQLite database.
        """
        conn = sqlite3.connect(DB_PATH)
        module_name = 'SubtensorModule'
        subnet_owner_coldkeys = get_subnet_owner_coldkeys(module_name)
        cursor = conn.cursor()

        cursor.execute('DROP TABLE IF EXISTS owners')

        cursor.execute('''
        CREATE TABLE owners (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            net_uid TEXT,
            owner_coldkey TEXT
        )
        ''')
        for owner in subnet_owner_coldkeys:
            for key, value in owner.items():
                cursor.execute('''
                INSERT INTO owners (net_uid, owner_coldkey)
                VALUES (?, ?)
                ''', (key, value))
        conn.commit()
        logging.info("Owner coldkeys table is updated")

    def update_whole_validator_coldkeys(self):
        """
        Fetches validator coldkeys, hotkeys, and amounts from the API and saves them to the SQLite database.
        """  
        
        url = "https://api.taostats.io/api/v1/validator"
        headers = {
            "accept": "application/json",
            "Authorization": self.TAOSTATS_API_KEY
        }

        all_validators = self.fetch_all_validators(url, headers)

        validator_coldkeys = []
        validator_hotkeys = []
        validator_amounts = []
        validator_names = []
        for validator in all_validators:
            amount = validator['amount']
            if int(amount) > 1000:
                validator_coldkeys.append(validator['cold_key']['ss58'])
                validator_hotkeys.append(validator['hot_key']['ss58'])
                name = self.get_validator_names(validator['hot_key']['ss58'])
                validator_names.append(name)
                validator_amounts.append(amount)
                
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('DROP TABLE IF EXISTS validators')

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS validators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cold_key TEXT,
            hot_key TEXT,
            amount TEXT,
            name TEXT
        )
        ''')

        for cold_key, hot_key, amount, name in zip(validator_coldkeys, validator_hotkeys, validator_amounts, validator_names):
            try:
                if name == None:
                    name = 'Unknown'
                cursor.execute('''
                INSERT INTO validators (cold_key, hot_key, amount, name)
                VALUES (?, ?, ?, ?)
                ''', (cold_key, hot_key, amount, name))
            except sqlite3.Error as e:
                logging.exception(f"Error inserting data : {e}")
        conn.commit()
        logging.info("validator coldkeys table is updated")

    def get_validator_names(self, hotkey):
        
        url = f"https://api.taostats.io/api/v1/delegate/info?address={hotkey}"
        headers = {
            "accept": "application/json",
            "Authorization": self.TAOSTATS_API_KEY
        }

        response = requests.get(url, headers=headers)
        if response.status_code == 429:  # Rate limit error
            time.sleep(20)  # Wait for 20 seconds before retrying
            return self.get_validator_names(hotkey)  # Retry the request
        
        response = response.json()
        if response["count"] == 1:
            return response["delegates"][0]["name"]
        else:
            return None
        
db_manager = DBManager()