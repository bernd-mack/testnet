import pandas as pd
from requests import get
from os import path, makedirs
from logging import basicConfig, info, INFO
from subfunctions import create_connection_rpc, read_deficonf, save_json_to_www, GLOBAL_INDEX_PHP, get_servername
from credentials import DEFICONF, WWW_DIR, TELEGRAM_CHATID_STATUS, TELEGRAM_CHATID_ALARM, TELEGRAM_TOKEN


# variables
SUBFOLDER = "listmasternodes"
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

try:
    rpc_connection = create_connection_rpc(read_deficonf(DEFICONF))

# get the current blockheight
    height = rpc_connection.getblockcount()

#get the current list of listmasternodes from the defid daemon
    listmasternodes = rpc_connection.listmasternodes({"including_start": True},True)
    print(f"Summe Masternodes: {len(listmasternodes)}")
    info(f"Summe Masternodes: {len(listmasternodes)}")
# load the list of listmasternodes into a pandas dataframe for easier sorting
    df=pd.DataFrame(listmasternodes)

    df = df.transpose().sort_values(by=['creationHeight'],ascending=False)

# remove not needed columns to reduce downloadsize
    del df['banTx']
    del df['localMasternode']
    del df['ownerIsMine']
    del df['operatorIsMine']

# filter the enabled, preenabled, resigned and preresigned masternode into extra dataframes
    df_enabled = df.loc[(df.state == "ENABLED")]
    print(f"ENABLED:       {len(df_enabled):5}")
    df_pre_enabled = df.loc[(df.state == "PRE_ENABLED")]
    print(f"PRE_ENABLED:   {len(df_pre_enabled):5}")
    df_resigned = df.loc[(df.state == "RESIGNED")]
    print(f"RESIGNED:      {len(df_resigned):5}")
    df_pre_resigned = df.loc[(df.state == "PRE_RESIGNED")]
    print(f"PRE_RESIGNED:  {len(df_pre_resigned):5}")

# create folder if not existant and prepare with standard index.php
    phpfile = open(directory+"/index_listmasternodes.php", "r")
    index_listmasternodes = phpfile.read()
    phpfile.close()

    if not path.exists(WWW_DIR+"/"+SUBFOLDER):
        makedirs(WWW_DIR+"/"+SUBFOLDER)
        phpfileobject = open(WWW_DIR+"/"+SUBFOLDER+"/index.php", 'w')
        phpfileobject.write(index_listmasternodes)
        phpfileobject.close()

    if not path.isfile(WWW_DIR+"/index.php"):
        phpfileobject = open(WWW_DIR+"/index.php", 'w')
        phpfileobject.write(GLOBAL_INDEX_PHP)
        phpfileobject.close()

# export the masternode lists to the www directory as json files
    df.transpose().to_json             (WWW_DIR+"/"+SUBFOLDER+"/listmasternodes.json")
    df_enabled.transpose().to_json     (WWW_DIR+"/"+SUBFOLDER+"/listmasternodes_enabled.json")
    df_resigned.transpose().to_json    (WWW_DIR+"/"+SUBFOLDER+"/listmasternodes_resigned.json")
    df_pre_enabled.transpose().to_json (WWW_DIR+"/"+SUBFOLDER+"/listmasternodes_pre_enabled.json")
    df_pre_resigned.transpose().to_json(WWW_DIR+"/"+SUBFOLDER+"/listmasternodes_pre_resigned.json")

    get(f'https://api.telegram.org/{TELEGRAM_TOKEN}/sendMessage?chat_id={TELEGRAM_CHATID_STATUS}&text={len(listmasternodes)} masternodes collected on {servername} {ip_address} at block {height}\n')

except Exception as e:
    print (e)
    get(f'https://api.telegram.org/{TELEGRAM_TOKEN}/sendMessage?chat_id={TELEGRAM_CHATID_ALARM}&text=Problems with {filename} on {servername} {ip_address} at block {height}\n {e}')
