import time
import random
import json
import requests
from web3 import Web3
from eth_account import Account

with open('abi.json') as file:
    abi = json.load(file)

w3 = Web3(Web3.HTTPProvider('https://rpc.linea.build'))

contract_address = '0xAd626D0F8BE64076C4c27a583e3df3878874467E'
value = Web3.to_wei(0, 'ether')

def get_random_gas_limit(min_gas, max_gas):
    return random.randint(min_gas, max_gas)

def read_private_keys(filename):
    with open(filename, 'r') as file:
        private_keys = file.readlines()
    return [key.strip() for key in private_keys]

def get_random_expiry():
    current_time = int(time.time())
    random_seconds = random.randint(3600, 7200)  
    expiry_time = current_time + random_seconds
    return expiry_time

def get_voucher_and_signature(address):
    url = 'https://public-api.phosphor.xyz/v1/purchase-intents'
    payload = {
        'buyer': {
            'eth_address': address
        },
        'listing_id': 'fceb2be9-f9fd-458a-8952-9a0a6f873aff',
        'provider': 'MINT_VOUCHER',
        'quantity': 1
    }
    headers = {
        'Content-Type': 'application/json',
    }

    while True:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 201:
            data = response.json()
            signature = data['data']['signature']
            voucher = data['data']['voucher']
            return voucher, signature
        else:
            print("No signature returned. Retrying...")
            time.sleep(1)  # Wait before retrying

def map_voucher_keys(voucher):
    return {
        'netRecipient': voucher['net_recipient'],
        'initialRecipient': voucher['initial_recipient'],
        'initialRecipientAmount': int(voucher['initial_recipient_amount']),
        'quantity': int(voucher['quantity']),
        'nonce': int(voucher['nonce']),
        'expiry': int(voucher['expiry']),
        'price': int(voucher['price']),
        'tokenId': int(voucher['token_id']),
        'currency': voucher['currency']
    }

private_keys = read_private_keys('private_keys.txt')
random.shuffle(private_keys)

contract = w3.eth.contract(address=contract_address, abi=abi)

successful_accounts = []

for private_key in private_keys:
    account = Account.from_key(private_key)
    nonce = w3.eth.get_transaction_count(account.address)

    voucher, signature = get_voucher_and_signature(account.address)

    print(f"Voucher: {voucher}")
    print(f"Signature: {signature}")

    mapped_voucher = map_voucher_keys(voucher)

    tx = contract.functions.mintWithVoucher(mapped_voucher, signature).build_transaction({
        'chainId': 59144,
        'gas': get_random_gas_limit(200000, 300000),
        'gasPrice': w3.eth.gas_price,
        'value': value,
        'nonce': nonce,
    })

    print(f"Transaction: {tx}")

    signed_tx = w3.eth.account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"Транзакция от аккаунта {account.address} успешно отправлена и подтверждена. Hash: {tx_hash.hex()}")

    successful_accounts.append(account.address)

    random_delay = random.uniform(350, 500)
    rounded_delay = round(random_delay)
    print(f"Ожидаю {rounded_delay} сек. перед следующим аккаунтом")
    time.sleep(rounded_delay)

with open('successful.txt', 'w') as file:
    for account_address in successful_accounts:
        file.write(f"{account_address}\n")
