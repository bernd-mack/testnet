from decimal import *
from requests import get
from os import path, makedirs
from logging import basicConfig, info, INFO
from subfunctions import create_connection_rpc, read_deficonf, save_json_to_www, GLOBAL_INDEX_PHP, get_servername
from credentials import DEFICONF, WWW_DIR, TELEGRAM_CHATID_STATUS, TELEGRAM_CHATID_ALARM, TELEGRAM_TOKEN

# variables
SUBFOLDER = "vaultaggregation"
filename = path.basename(__file__)
directory = path.dirname(__file__)
logfile = path.dirname(__file__)+"/"+filename.split(".")[0]+".log"

# program start
basicConfig(filename=logfile, format='%(asctime)s - %(message)s', level=INFO)
info("######################################")
info(f"Start {filename}")

# get ip address
servername, ip_address = get_servername()
height = "n/a"

data = [{"state": "active",        "collateralAmounts": {}, "loanAmounts": {}, "interestAmounts": {}},
        {"state": "inLiquidation", "collateralAmounts": {}, "loanAmounts": {}}]

try:
    rpc_connection = create_connection_rpc(read_deficonf(DEFICONF))

# get the current blockheight
    height = rpc_connection.getblockcount()

    vaultlist = rpc_connection.listvaults({}, {"limit":100000})
    info(f"Anzahl Vaults: {len(vaultlist)}")

    for i in vaultlist:
        vault = rpc_connection.getvault(i["vaultId"])
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

    info (data)
    print (data)
    save_json_to_www(WWW_DIR, "vaultaggregation", data)
    
    loandusd = 0
    if "DUSD" in data[0]["interestAmounts"]:
        loandusd+=data[0]["interestAmounts"]["DUSD"]
    if "DUSD" in data[0]["loanAmounts"]:
        loandusd+=data[0]["loanAmounts"]["DUSD"]
    if "DUSD" in data[1]["loanAmounts"]:
        loandusd+=data[1]["loanAmounts"]["DUSD"]


except Exception as e:
    print (e)
    get(f'https://api.telegram.org/{TELEGRAM_TOKEN}/sendMessage?chat_id={TELEGRAM_CHATID_ALARM}&text=Problems with {filename} on {servername} {ip_address} at block {height}\n {e}')
