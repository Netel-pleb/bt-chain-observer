import pytest
from unittest.mock import patch, MagicMock
import sqlite3
from db_manage.db_manager import DBManager
@pytest.fixture
def db_manager():
    """ Fixture to create a DBManager instance for testing. """
    manager = DBManager()
    yield manager

def test_create_table_if_not_exist(db_manager):
    """ Test table creation. """
    with patch('sqlite3.connect') as mock_connect:
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        mock_cursor = mock_conn.cursor.return_value
        
        db_manager.create_table_if_not_exist("test_table")
        
        mock_cursor.execute.assert_called_with('''
        CREATE TABLE IF NOT EXISTS test_table (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            current_block_number TEXT
        )
        ''')

def test_get_validator_name(db_manager):
    """ Test retrieving validator name. """
    with patch('sqlite3.connect') as mock_connect:
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        mock_cursor = mock_conn.cursor.return_value
        
        # Mock the database response
        mock_cursor.fetchone.return_value = ('ValidatorName', 'HotKey')
        
        name, hot_key, status = db_manager.get_validator_name('some_coldkey')
        
        assert name == 'ValidatorName'
        assert hot_key == 'HotKey'
        assert status == 1

def test_get_owner_netuid(db_manager):
    """ Test retrieving owner netuid. """
    with patch('sqlite3.connect') as mock_connect:
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        mock_cursor = mock_conn.cursor.return_value
        
        # Mock the database response
        mock_cursor.fetchone.return_value = ('NetUid',)
        
        netuid = db_manager.get_owner_netuid('some_coldkey')
        
        assert netuid == 'NetUid'

def test_update_validator_coldkey(db_manager):
    """ Test updating validator coldkey. """
    with patch('sqlite3.connect') as mock_connect:
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn
        mock_cursor = mock_conn.cursor.return_value
        
        db_manager.update_validator_coldkey('old_key', 'new_key')
        
        mock_cursor.execute.assert_called_with('UPDATE validators SET cold_key = ? WHERE cold_key = ?', ('new_key', 'old_key'))
        mock_conn.commit.assert_called()

