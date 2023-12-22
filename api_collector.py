from os import path
from logging import basicConfig, info, INFO
from requests import post, get
from credentials import WWW_DIR, DEFID, DATA_DIR, DEFICONF, API_LIST, TELEGRAM_TOKEN, TELEGRAM_CHATID_ALARM, TELEGRAM_CHATID_STATUS, NETWORK
from subfunctions import save_json_to_www, get_systeminfo, get_version, get_credentials_from_config
from subfunctions import remove_unused_dirs, api_calls, get_operators, get_servername
from json import dumps
from datetime import datetime

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

def get_vmmap():
    returnvalue = 0
    blockcount = str(rpc("getblockcount", []))
    returnvalue = rpc("vmmap", [blockcount, 0])
    return returnvalue

errors = False

#TODO put a try, except around the special functions or direct in the subfunctions
KEEP_DIRECTORYS = ["systeminfo", "version", "operatoraddresses", "listmasternodes", "vaultaggregation", "statistics", "statistics_v2", "rpc_status", "getblockcountevm"]
save_json_to_www(WWW_DIR, "systeminfo",        get_systeminfo(DATA_DIR))
save_json_to_www(WWW_DIR, "version",           get_version(DEFID))
save_json_to_www(WWW_DIR, "operatoraddresses", get_operators(DEFICONF))
save_json_to_www(WWW_DIR, "getblockcountevm",  get_vmmap())

try:
    functions = api_calls(API_LIST)
except Exception as e:
    functions = {}
    print (f'api_calls() {str(e)}')

if functions:
    for i in functions:
        print (f'{i} {functions[i]}')
        info (f'{i} {functions[i]}')
        try:
            start = datetime.now()
            save_json_to_www(WWW_DIR, i, rpc(i, functions[i]))
            print (f"=> time: {datetime.now()-start}")
            info (f"=> time: {datetime.now()-start}")
        except Exception as err:
            text = f"Problems with {filename} on {servername} {ip_address}\n{i} {err}"
            print (text)
            info (text)
            if not errors:
                get(f'https://api.telegram.org/{TELEGRAM_TOKEN}/sendMessage?chat_id={TELEGRAM_CHATID_ALARM}&text={text}')
                errors = True
else:
    get(f'https://api.telegram.org/{TELEGRAM_TOKEN}/sendMessage?chat_id={TELEGRAM_CHATID_ALARM}&text=Nothing to collect.')

print(f'removed directorys: {remove_unused_dirs(WWW_DIR, list(functions.keys()) + KEEP_DIRECTORYS)}')
info(f'removed directorys: {remove_unused_dirs(WWW_DIR, list(functions.keys()) + KEEP_DIRECTORYS)}')

get(f'https://api.telegram.org/{TELEGRAM_TOKEN}/sendMessage?chat_id={TELEGRAM_CHATID_STATUS}&text=Runtime {filename} {servername} {ip_address}: {datetime.now()-starttime} ')

info(f"End {filename} in {datetime.now()-starttime}")
print(f"End {filename} in {datetime.now()-starttime}")
