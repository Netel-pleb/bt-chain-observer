from substrateinterface.utils.ss58 import ss58_encode
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def convert_hex_to_ss58(hex_address):
    if hex_address.startswith('0x'):
        hex_address = hex_address[2:]
    address_bytes = bytes.fromhex(hex_address)
    ss58_address = ss58_encode(address_bytes)
    return ss58_address

if __name__ == '__main__':
    hex_address = '0x64e51387c629f7852195fde79cc7c5119c7ee4bbc0da3a7f3e9ee926d6fd955f'
    ss58_address = convert_hex_to_ss58(hex_address)
    logging.info(ss58_address)

