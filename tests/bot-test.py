import pytest
from unittest.mock import MagicMock, patch
from chain_observer.bot.bt_chain_observer import BtChainObserver

@pytest.fixture
def observer():
    """Fixture to create a BtChainObserver instance with a mocked DBManager."""
    with patch('db_manage.db_manager') as MockDBManager:
        mock_db_manager = MockDBManager.return_value
        observer_instance = BtChainObserver()
        observer_instance.db_manager = mock_db_manager
        return observer_instance

def test_setup_substrate_interface_success(observer):
    """Test successful setup of the Substrate interface."""
    with patch('substrateinterface.base.SubstrateInterface') as MockSubstrateInterface:
        MockSubstrateInterface.return_value = MagicMock()
        substrate = observer.setup_substrate_interface()
        assert substrate is not None

def test_get_block_data_success(observer):
    """Test fetching block data successfully."""
    observer.substrate = MagicMock()
    observer.substrate.get_block_hash.return_value = 'mock_block_hash'
    observer.substrate.get_block.return_value = {'extrinsics': []}
    observer.substrate.get_events.return_value = [{'mock': 'event'}]

    block, events = observer.get_block_data(1)
    assert block == {'extrinsics': []}
    assert events == [{'mock': 'event'}]

def test_get_block_data_failure(observer):
    """Test fetching block data when it fails."""
    observer.substrate = MagicMock()
    observer.substrate.get_block_hash.side_effect = Exception("Block not found")

    block, events = observer.get_block_data(1)
    assert block is None
    assert events is None

def test_extract_block_timestamp_from_extrinsics(observer):
    """Test extracting block timestamp from extrinsics."""
    extrinsics = [
        MagicMock(value={
            'call': {
                'call_function': 'set',
                'call_module': 'Timestamp',
                'call_args': [{'value': 1638316800000}]
            }
        })
    ]
    timestamp = observer.extract_block_timestamp_from_extrinsics(extrinsics)
    assert timestamp == '2021-12-01 00:00:00 (UTC+00:00)'

def test_extract_block_timestamp_from_extrinsics_no_timestamp(observer):
    """Test extracting block timestamp from extrinsics when no timestamp is present."""
    extrinsics = [
        MagicMock(value={
            'call': {
                'call_function': 'other_function',
                'call_module': 'OtherModule'
            }
        })
    ]
    timestamp = observer.extract_block_timestamp_from_extrinsics(extrinsics)
    assert timestamp is None

def test_find_extrinsic_indices(observer):
    """Test finding indices of specific extrinsics."""
    extrinsics = [
        MagicMock(value={'call': {'call_function': 'schedule_swap_coldkey', 'call_module': 'SubtensorModule'}}),
        MagicMock(value={'call': {'call_function': 'schedule_dissolve_network', 'call_module': 'SubtensorModule'}}),
        MagicMock(value={'call': {'call_function': 'vote', 'call_module': 'SubtensorModule'}})
    ]
    indices = observer.find_extrinsic_indices(extrinsics, 'schedule_swap_coldkey', 'schedule_dissolve_network', 'vote', 'SubtensorModule')
    assert indices == (0, 1, 2)

def test_find_extrinsic_indices_not_found(observer):
    """Test finding indices of specific extrinsics when they are not found."""
    extrinsics = [
        MagicMock(value={'call': {'call_function': 'other_function', 'call_module': 'OtherModule'}})
    ]
    indices = observer.find_extrinsic_indices(extrinsics, 'schedule_swap_coldkey', 'schedule_dissolve_network', 'vote', 'SubtensorModule')
    assert indices == (-1, -1, -1)

def test_collect_extrinsic_events_and_status(observer):
    """Test collecting extrinsic events and determining success status."""
    events = [
        MagicMock(value={'extrinsic_idx': 0, 'event_id': 'ExtrinsicSuccess'}),
        MagicMock(value={'extrinsic_idx': 0, 'event_id': 'OtherEvent'})
    ]
    extrinsic_events, extrinsic_success = observer.collect_extrinsic_events_and_status(events, 0)
    assert len(extrinsic_events) == 2
    assert extrinsic_success is True

def test_collect_extrinsic_events_and_status_failure(observer):
    """Test collecting extrinsic events and determining failure status."""
    events = [
        MagicMock(value={'extrinsic_idx': 0, 'event_id': 'ExtrinsicFailed'})
    ]
    extrinsic_events, extrinsic_success = observer.collect_extrinsic_events_and_status(events, 0)
    assert len(extrinsic_events) == 1
    assert extrinsic_success is False

def test_extract_vote_details(observer):
    """Test extracting vote details from an extrinsic."""
    extrinsic = MagicMock(value={
        'call': {
            'call_args': [
                {'name': 'hotkey', 'value': 'mock_hotkey'},
                {'name': 'proposal', 'value': 'mock_proposal'},
                {'name': 'approve', 'value': True},
                {'name': 'index', 'value': 1}
            ]
        }
    })
    hotkey, proposal, approve, index = observer.extract_vote_details(extrinsic)
    assert hotkey == 'mock_hotkey'
    assert proposal == 'mock_proposal'
    assert approve is True
    assert index == 1

def test_extract_vote_details_missing(observer):
    """Test extracting vote details when they are missing from an extrinsic."""
    extrinsic = MagicMock(value={
        'call': {
            'call_args': []
        }
    })
    hotkey, proposal, approve, index = observer.extract_vote_details(extrinsic)
    assert hotkey is None
    assert proposal is None
    assert approve is None
    assert index is None

def test_find_swapped_coldeky_and_dissolved_network(observer):
    """Test finding swapped coldkeys and dissolved networks in events."""
    events = [
        MagicMock(value={'event_id': 'ColdkeySwapped', 'attributes': {'old_coldkey': 'old', 'new_coldkey': 'new'}}),
        MagicMock(value={'event_id': 'NetworkRemoved', 'attributes': 'netuid'})
    ]
    old_coldkey, new_coldkey, netuid = observer.find_swapped_coldeky_and_dissolved_network(events, 'ColdkeySwapped', 'NetworkRemoved')
    assert old_coldkey == 'old'
    assert new_coldkey == 'new'
    assert netuid == 'netuid'

def test_find_swapped_coldeky_and_dissolved_network_not_found(observer):
    """Test finding swapped coldkeys and dissolved networks when not found in events."""
    events = [
        MagicMock(value={'event_id': 'OtherEvent', 'attributes': {}})
    ]
    old_coldkey, new_coldkey, netuid = observer.find_swapped_coldeky_and_dissolved_network(events, 'ColdkeySwapped', 'NetworkRemoved')
    assert old_coldkey is None
    assert new_coldkey is None
    assert netuid is None
