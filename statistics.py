import pandas as pd     #pip install pandas
from requests import get, post # pip install requests
from json import dumps
from os import path, makedirs
from logging import basicConfig, info, INFO
from subfunctions import save_json_to_www, GLOBAL_INDEX_PHP, get_servername, get_credentials_from_config
from subfunctions import get_serverlist_txt, get_mininginfo, get_operatorlist_txt, add_operator_to_list
from credentials import DEFICONF, WWW_DIR, TELEGRAM_CHATID_STATUS, TELEGRAM_CHATID_ALARM, TELEGRAM_TOKEN, NETWORK
from datetime import datetime

# variables
starttime = datetime.now()
filename = path.basename(__file__)
directory = path.dirname(__file__)
logfile = path.dirname(__file__)+"/"+filename.split(".")[0]+".log"

# program start
basicConfig(filename=logfile, format='%(asctime)s - %(message)s', level=INFO)
info("######################################")
info(f"Start {filename}")

cred = get_credentials_from_config(DEFICONF, network=NETWORK)

url = f'http://{cred["rpcbind"]}:{cred["rpcport"]}'

def rpc(method, params=[]):
    payload = dumps({
        "jsonrpc": "2.0",
        "id": " mydefichain",
        "method": method,
        "params": params
    })
    response = post(url, auth=(cred["rpcuser"], cred["rpcpass"]), data=payload).json()['result']
    return response

#######################################
# get ip address
servername, ip_address = get_servername()
height = "n/a"

data = [{"masternodes": {"ENABLED": 0, "PRE_ENABLED": 0, "RESIGNED": 0, "PRE_RESIGNED": 0}},
        {"timelock": {"5 years": 0, "10 years": 0, "none": 0}},
        {"server": {"ONLINE": 0, "OFFLINE": 0}}]

errorlist = []
try:
# get the current blockheight
    height = rpc("getblockcount")

    operatorlist = get_operatorlist_txt(directory+"/operatorlist.txt")
    listmasternodes = rpc("listmasternodes", [{"including_start": True}, True])

# get serverlist and check if new operatoraddresses are found, create Online and Offline Serverinformation in data structure
    serverlist = get_serverlist_txt(directory+"/serverlist_mainnet.txt")
    for server in serverlist:
        mininginfo = get_mininginfo(server, errorlist)
        if "isoperator" in mininginfo:
            isoperator = mininginfo["isoperator"]
        if "masternodes" in mininginfo:
            for i in mininginfo["masternodes"]:
                if i["operator"] not in operatorlist:
                    print(f'new operator found: {i["operator"]} on {server["host"]}')
                    info(f'new operator found: {i["operator"]} on {server["host"]}')
                    operatorlist.append(i["operator"])
                    add_operator_to_list(directory+"/operatorlist.txt", i["operator"])

    data[2]["server"]["ONLINE"]  = len(serverlist)-len(errorlist)
    data[2]["server"]["OFFLINE"] = len(errorlist)

    temp_operatorlist = []
    for masternode in listmasternodes:
        temp_operatorlist.append(listmasternodes[masternode]["operatorAuthAddress"])
        if listmasternodes[masternode]["operatorAuthAddress"] in operatorlist:
            if listmasternodes[masternode]["state"] == "ENABLED":
                data[0]["masternodes"]["ENABLED"]+=1
                if "timelock" in listmasternodes[masternode]:
                    if listmasternodes[masternode]["timelock"] == "10 years": data[1]["timelock"]["10 years"]+=1
                    elif listmasternodes[masternode]["timelock"] == "5 years": data[1]["timelock"]["5 years"]+=1
                else: data[1]["timelock"]["none"]+=1
            elif listmasternodes[masternode]["state"] == "PRE_ENABLED":
                data[0]["masternodes"]["PRE_ENABLED"]+=1
                if "timelock" in listmasternodes[masternode]:
                    if listmasternodes[masternode]["timelock"] == "10 years": data[1]["timelock"]["10 years"]+=1
                    elif listmasternodes[masternode]["timelock"] == "5 years": data[1]["timelock"]["5 years"]+=1
                else: data[1]["timelock"]["none"]+=1
            elif listmasternodes[masternode]["state"] == "PRE_RESIGNED": data[0]["masternodes"]["PRE_RESIGNED"]+=1
            elif listmasternodes[masternode]["state"] == "RESIGNED": data[0]["masternodes"]["RESIGNED"]+=1

    info (data)
    save_json_to_www(WWW_DIR, "statistics", data)

except Exception as e:
    print (e)
    get(f'https://api.telegram.org/{TELEGRAM_TOKEN}/sendMessage?chat_id={TELEGRAM_CHATID_ALARM}&text=Problems with {filename} on {servername} {ip_address} at block {height}\n {e}')

get(f'https://api.telegram.org/{TELEGRAM_TOKEN}/sendMessage?chat_id={TELEGRAM_CHATID_STATUS}&text=Runtime {filename} {servername} {ip_address}: {datetime.now()-starttime} ')

info(f"End {filename} in {datetime.now()-starttime}")
print(f"End {filename} in {datetime.now()-starttime}")
