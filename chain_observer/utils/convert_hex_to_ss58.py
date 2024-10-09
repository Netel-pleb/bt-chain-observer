from substrateinterface import Keypair

def convert_hex_to_ss58(hex_string: str, ss58_format: int = 42) -> str:

    public_key_hex = hex_string[-64:]
    
    public_key = bytes.fromhex(public_key_hex)
    
    if len(public_key) != 32:
        raise ValueError('Public key should be 32 bytes long')
    
    keypair = Keypair(public_key=public_key, ss58_format=ss58_format)
    return keypair.ss58_address