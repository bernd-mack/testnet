from os import path
from web3 import Web3 # pip install web3
from subfunctions import save_json_to_www, get_servername
from credentials import WWW_DIR
from logging import basicConfig, info, INFO
from datetime import datetime
import json

# variables
starttime = datetime.now()
filename = path.basename(__file__)
directory = path.dirname(__file__)
logfile = path.dirname(__file__)+"/"+filename.split(".")[0]+".log"
servername, ip_address = get_servername()

# program start
basicConfig(filename=logfile, format='%(asctime)s - %(message)s', level=INFO)
info("######################################")
info(f"Start {filename}")

# Pfad zur JSON-Datei
json_file_path = directory+"/web3api.json"

# JSON-Datei einlesen
with open(json_file_path, 'r') as file:
    data = json.load(file)

for cnt, i in enumerate(data):
    connected = False
    block = hash = chainId = peers = response_time ="n/a"

    web3 = Web3(Web3.HTTPProvider(i["url"], request_kwargs={'timeout': 10}))
    try:
        block = web3.eth.get_block_number()
        connected = True
    except Exception as err:
        print(err)

    if connected:
        try:
            chainId = web3.eth.chain_id
        except Exception as err:
            print(err)

        try:
            hash = web3.eth.get_block(block)['hash'].hex()
        except Exception as err:
            print(err)

        try:
            peers = web3.net.peer_count
        except Exception as err:
            print(err)

    print(f"Info:     {i['name']}")
    print(f"Block:    {block}")
    print(f"Hash:     {hash}")
    print(f"ChainId:  {chainId}")
    print(f"Peers:    {peers}")
    print(f"Ping:     {response_time}")
    
    if "hide_url" in i and i["hide_url"]:
        data[cnt]["url"] = "hidden"
    
    print("######################")
    data[cnt]["hash"] = hash
    data[cnt]["block"] = block
    data[cnt]["chainId"] = chainId
    data[cnt]["peers"] = peers
    data[cnt]["ping"] = response_time


save_json_to_www(WWW_DIR, "rpc_status", data)

info(f"End {filename} in {datetime.now()-starttime}")
print(f"End {filename} in {datetime.now()-starttime}")
