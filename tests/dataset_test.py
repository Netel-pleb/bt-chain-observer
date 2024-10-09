import pytest
from unittest.mock import patch
from db_manage.db_manager import DBManager

@pytest.fixture
def db_manager():
    """Fixture to create a DBManager instance with an in-memory SQLite database."""
    manager = DBManager(':memory:')
    yield manager
    manager.conn.close()

def test_create_table_if_not_exist(db_manager):
    """Test that a table is created if it does not exist."""
    db_manager.create_table_if_not_exist('test_table')
    db_manager.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='test_table'")
    assert db_manager.cursor.fetchone() is not None, "Table 'test_table' should exist."

def test_get_validator_name(db_manager):
    """Test retrieving a validator's name by cold key."""
    db_manager.cursor.execute('''
        CREATE TABLE validators (
            id INTEGER PRIMARY KEY, 
            cold_key TEXT, 
            hot_key TEXT, 
            name TEXT
        )
    ''')
    db_manager.cursor.execute('''
        INSERT INTO validators (cold_key, hot_key, name) 
        VALUES (?, ?, ?)
    ''', ('test_coldkey', 'testhotkey', 'Test Validator'))
    db_manager.conn.commit()
    name, hot_key, status = db_manager.get_validator_name('test_coldkey')
    assert name == 'Test Validator', "Validator name should match."
    assert hot_key == 'testhotkey', "Hot key should match."
    assert status == 1, "Status should be 1."

def test_verify_update_block_number(db_manager):
    """Test verifying and updating the block number."""
    db_manager.verify_update_block_number(1)
    db_manager.cursor.execute('SELECT current_block_number FROM block_number_table')
    result = db_manager.cursor.fetchone()
    assert result[0] == '1', "Block number should be updated to '1'."

    with patch('sentry_sdk.capture_exception') as mock_sentry:
        db_manager.verify_update_block_number(3)
        mock_sentry.assert_called_once(), "Exception should be captured once."

def test_update_validator_coldkey(db_manager):
    """Test updating a validator's cold key."""
    db_manager.cursor.execute('''
        CREATE TABLE validators (
            id INTEGER PRIMARY KEY, 
            cold_key TEXT
        )
    ''')
    db_manager.cursor.execute('INSERT INTO validators (cold_key) VALUES (?)', ('old_coldkey',))
    db_manager.conn.commit()

    db_manager.update_validator_coldkey('old_coldkey', 'new_coldkey')
    db_manager.cursor.execute('SELECT cold_key FROM validators WHERE cold_key = ?', ('new_coldkey',))
    assert db_manager.cursor.fetchone() is not None, "Cold key should be updated to 'new_coldkey'."

def test_update_owner_coldkey(db_manager):
    """Test updating an owner's cold key."""
    db_manager.cursor.execute('''
        CREATE TABLE owners (
            id INTEGER PRIMARY KEY, 
            net_uid TEXT, 
            owner_coldkey TEXT
        )
    ''')
    
    db_manager.cursor.execute('INSERT INTO owners (net_uid, owner_coldkey) VALUES (?, ?)', ('netuid1', 'old_coldkey'))
    db_manager.conn.commit()

    db_manager.update_owner_coldkey('netuid1', 'new_coldkey')
    db_manager.cursor.execute('SELECT owner_coldkey FROM owners WHERE net_uid = ?', ('netuid1',))
    assert db_manager.cursor.fetchone()[0] == 'new_coldkey', "Owner cold key should be updated to 'new_coldkey'."

if __name__ == '__main__':
    pytest.main()
