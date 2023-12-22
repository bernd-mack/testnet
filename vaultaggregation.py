from decimal import *
from requests import get, post
from os import path
from logging import basicConfig, info, INFO
from subfunctions import save_json_to_www, GLOBAL_INDEX_PHP, get_servername, get_credentials_from_config
from credentials import DEFICONF, WWW_DIR, TELEGRAM_CHATID_STATUS, TELEGRAM_CHATID_ALARM, TELEGRAM_TOKEN, NETWORK
from datetime import datetime
from json import dumps

# variables
SUBFOLDER = "vaultaggregation"
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

# get ip address
servername, ip_address = get_servername()
height = "n/a"

data = [{"state": "active",        "collateralAmounts": {}, "loanAmounts": {}, "interestAmounts": {}},
        {"state": "inLiquidation", "collateralAmounts": {}, "loanAmounts": {}}]

try:
# get the current blockheight
    height = rpc("getblockcount")

    vaultlist = rpc("listvaults", [{}, {"limit":100000}])
    info(f"Anzahl Vaults: {len(vaultlist)}")

    for cnt, i in enumerate(vaultlist):
        print(f"{cnt:5} / {len(vaultlist)}",end="\r")
        vault = rpc("getvault", [i["vaultId"]])
        if "state" in vault:
            if vault["state"] == "active":
                for collaterals in vault["collateralAmounts"]:
                    amount, token = collaterals.split("@")
                    if token in data[0]["collateralAmounts"]: data[0]["collateralAmounts"][token] += Decimal(amount)
                    else: data[0]["collateralAmounts"][token] = Decimal(amount)

                for loans in vault["loanAmounts"]:
                    amount, token = loans.split("@")
                    if token in data[0]["loanAmounts"]: data[0]["loanAmounts"][token] += Decimal(amount)
                    else: data[0]["loanAmounts"][token] = Decimal(amount)

                for interests in vault["interestAmounts"]:
                    amount, token = interests.split("@")
                    if token in data[0]["interestAmounts"]: data[0]["interestAmounts"][token] += Decimal(amount)
                    else: data[0]["interestAmounts"][token] = Decimal(amount)

            elif vault["state"] == "inLiquidation":
                for batch in vault["batches"]:
                    for collaterals in batch["collaterals"]:
                        print (collaterals)
                        amount, token = collaterals.split("@")
                        if token in data[1]["collateralAmounts"]: data[1]["collateralAmounts"][token] += Decimal(amount)
                        else: data[1]["collateralAmounts"][token] = Decimal(amount)

                    if "loan" in batch:
                        print (batch["loan"])
                        amount, token = batch["loan"].split("@")
                        if token in data[1]["loanAmounts"]: data[1]["loanAmounts"][token] += Decimal(amount)
                        else: data[1]["loanAmounts"][token] = Decimal(amount)
    print(" ")

    info (data)
    print (data)
    save_json_to_www(WWW_DIR, "vaultaggregation", data)

except Exception as e:
    print (e)
    get(f'https://api.telegram.org/{TELEGRAM_TOKEN}/sendMessage?chat_id={TELEGRAM_CHATID_ALARM}&text=Problems with {filename} on {servername} {ip_address} at block {height}\n {e}')

print("#####")

get(f'https://api.telegram.org/{TELEGRAM_TOKEN}/sendMessage?chat_id={TELEGRAM_CHATID_STATUS}&text=Vaultaggregation {servername} {ip_address} at block {height} in {len(vaultlist)} vaults at block {height} in {datetime.now()-starttime}')
info(f"End {filename} in {datetime.now()-starttime}")
