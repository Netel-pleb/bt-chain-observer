import bittensor as bt
from dotenv import load_dotenv
import os
import asyncio
import json
import websockets
from chain_observer.utils.convert_hex_to_ss58 import convert_hex_to_ss58

load_dotenv()

chain_endpoint = os.getenv("SUBTENSOR_ENDPOINT")

subtensor = bt.Subtensor(network=chain_endpoint)

async def rpc_requests(params):
    async with websockets.connect(
        chain_endpoint, ping_interval=None
    ) as ws:
        
        responses = []
        await ws.send(json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "state_subscribeStorage",
                'params': [params]
            }
        ))
        ignore = await ws.recv()  # Ignore the first response since it's just a confirmation
        response = await ws.recv()
        changes = json.loads(response)["params"]["result"]["changes"]
        responses.append(changes)
        return responses

def generate_params(module_hex_code, subnet_uids):
    """
    Generate a list of strings by appending hexadecimal representations of decimal numbers (1 to 52) to the original string.
    
    :param module_hex_code: The original string (e.g., '0x658faa385070e074c85bf6b568cf055536e3e82152c8758267395fe524fbbd16')
    :param subnet_uids: List of subnet UIDs
    :return: A list of strings with appended hex numbers
    """
    params = []
    for uid in subnet_uids:
        hex_suffix = hex(uid)[2:].zfill(2) + '00'  # Convert to hex and zero-fill to 2 digits
        params.append(module_hex_code + hex_suffix)

    return params

def get_subnet_owner_coldkeys(rpc_call_module_name):
    subnet_uids = subtensor.get_subnets()
    subnet_uids.remove(0)
    subtensor_module_hex_code = '0x658faa385070e074c85bf6b568cf055536e3e82152c8758267395fe524fbbd16'
    if rpc_call_module_name == 'SubtensorModule':
        module_hex_code = subtensor_module_hex_code
    params = generate_params(module_hex_code, subnet_uids)
    
    responses = asyncio.run(rpc_requests(params))
    
    owner_coldkeys = []
    response = responses[0]
    for uid, result in zip(subnet_uids, response):
        if result:  
            coldkey = convert_hex_to_ss58(result[1])
            owner_coldkeys.append({uid: coldkey}) 
    return owner_coldkeys

if __name__ == "__main__":
    get_subnet_owner_coldkeys()