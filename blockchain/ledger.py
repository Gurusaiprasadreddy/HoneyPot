import os
import json
from web3 import Web3
import solcx

GANACHE_URL = os.getenv("GANACHE_URL", "http://localhost:7545")
CONTRACT_PATH = "/app/contracts/HoneypotLogger.sol"  # Mounted in docker

w3 = Web3(Web3.HTTPProvider(GANACHE_URL))
contract_instance = None

def init_blockchain():
    global contract_instance
    if not w3.is_connected():
        print("Ganache not connected.")
        return False
        
    try:
        solcx.install_solc('0.8.0')
        compiled_sol = solcx.compile_files([CONTRACT_PATH], output_values=["abi", "bin"])
        contract_id, contract_interface = compiled_sol.popitem()
        
        abi = contract_interface['abi']
        bytecode = contract_interface['bin']
        
        account = w3.eth.accounts[0]
        w3.eth.default_account = account
        
        HoneypotLogger = w3.eth.contract(abi=abi, bytecode=bytecode)
        tx_hash = HoneypotLogger.constructor().transact()
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        contract_instance = w3.eth.contract(
            address=tx_receipt.contractAddress,
            abi=abi
        )
        print(f"Contract deployed at {tx_receipt.contractAddress}")
        return True
    except Exception as e:
        print(f"Failed to deploy contract: {e}")
        return False

def anchor_log(timestamp, ip, session_id, commands, attack_type, risk_score, log_hash):
    if not contract_instance:
        return False
    try:
        tx_hash = contract_instance.functions.storeLog(
            timestamp, ip, session_id, commands, attack_type, risk_score, log_hash
        ).transact()
        w3.eth.wait_for_transaction_receipt(tx_hash)
        return True
    except Exception as e:
        print(f"Blockchain write error: {e}")
        return False

def verify_log(log_hash):
    if not contract_instance:
        return False
    try:
        return contract_instance.functions.verifyLog(log_hash).call()
    except:
        return False