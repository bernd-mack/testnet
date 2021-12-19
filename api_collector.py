from os import path, makedirs, listdir
from subprocess import check_output
from json import JSONEncoder, dumps
from logging import basicConfig, info, INFO
from decimal import Decimal
from bitcoinrpc.authproxy import AuthServiceProxy
from socket import gethostbyname, gethostname
from psutil import virtual_memory, cpu_percent, cpu_freq, net_io_counters, cpu_count, disk_usage, disk_partitions
import shutil
import credentials

# psutil, shutil, python-bitcoinrpc, requests nicht Standardinstallation

# functions
class DecimalEncoder (JSONEncoder):
    def default (self, obj):
        if isinstance (obj, Decimal):
            return float (obj)
        return JSONEncoder.default (self, obj)

def read_deficonf(filename):
    returnvalue = {}
    with open(filename) as f:
        for i in f.read().split('\n'):
            if i.startswith("rpcuser"):
                returnvalue["rpcuser"]     = i.split("=")[1].strip(" ")
            elif i.startswith("rpcpassword"):
                returnvalue["rpcpassword"] = i.split("=")[1].strip(" ")
            elif i.startswith("rpcport"):
                returnvalue["rpcport"]     = i.split("=")[1].strip(" ")
            elif i.startswith("rpcbind"):
                returnvalue["rpcbind"]     = i.split("=")[1].strip(" ")
    return returnvalue

def save_json_to_www(folder, subfolder, data):
    if not path.exists(folder+"/"+subfolder):
        makedirs(folder+"/"+subfolder)
        phpfileobject = open(folder+"/"+subfolder+"/index.php", 'w')
        phpfileobject.write(API_INDEX_PHP)
        phpfileobject.close()
        #TODO 1 create empty data file
        #TODO 2 set chmod rights
        #TODO 3 set owner chown for new directory and file www-data

    if not path.isfile(folder+"/index.php"):
        phpfileobject = open(folder+"/index.php", 'w')
        phpfileobject.write(GLOBAL_INDEX_PHP)
        phpfileobject.close()

    json_data = dumps(data, cls = DecimalEncoder, sort_keys=True, indent=4)
    fileobject = open(folder+"/"+subfolder+"/data.json", 'w')
    fileobject.write(json_data)
    fileobject.close()
    return 0

def create_connection_rpc(secrets):
    url = "http://%s:%s@%s:%s/"%(secrets["rpcuser"], secrets["rpcpassword"], secrets["rpcbind"], secrets["rpcport"])
    return AuthServiceProxy(url)

def api_calls(filename):
    returnvalue = {}
    with open(filename) as f:
        for i in f.read().split('\n'):
            if i.startswith("=") or i.startswith("#"): #if header or commented, then skip
                continue
            if i:
                returnvalue[i.split(" ")[0]] = list(map(eval,i.split(" ")[1:]))
    return returnvalue

def remove_unused_dirs(folder, keep_dir):
    deleted = []
    for file in listdir(folder):
        if path.isdir(folder + "/" + file):
            if file.split("/")[-1] not in keep_dir:
                try:
                    shutil.rmtree(folder + "/" + file)
                    deleted.append(file)
                except OSError as e:
                    print(e)
                else:
                    info(f"The directory {file} is deleted successfully")
    return deleted

def get_systeminfo():
    stats_data = {"disk_total": 0, "disk_used": 0, "disk_free": 0}
    partitions = disk_partitions()
    for i in enumerate(partitions):
        try:
            space = disk_usage(partitions[i[0]].mountpoint)
            stats_data["disk_total"] += space.total
            stats_data["disk_used"] += space.used
            stats_data["disk_free"] += space.free
        except:
            continue

    stats_data["bytes_sent"]   = net_io_counters().bytes_sent
    stats_data["bytes_recv"]   = net_io_counters().bytes_recv
    stats_data["cpu_count"]    = cpu_count()
    stats_data["cpu_freq"]     = cpu_freq().current
    stats_data["cpu_load"]     = cpu_percent(interval=1, percpu=False)
    stats_data["memory_total"] = virtual_memory().total
    stats_data["memory_used"]  = virtual_memory().used
    stats_data["memory_free"]  = virtual_memory().free
    print (stats_data)
    return stats_data

def get_version(file):
    version = check_output([file, '--version'], encoding='UTF-8').split("\n")[0]
    print (version)
    return version

# variables
filename = path.basename(__file__)
directory = path.dirname(__file__)
logfile = path.dirname(__file__)+"/"+filename.split(".")[0]+".log"

API_INDEX_PHP = "<?PHP header('Content-Type: application/json');\n\n$data = file_get_contents('data.json');\n\necho $data;\n\n?>"
GLOBAL_INDEX_PHP = "<!DOCTYPE html>\n<html>\n<body>\n<?PHP\n$verzeichnis = '.';\n$verz_inhalt = scandir($verzeichnis);\nforeach ($verz_inhalt as $folder) {\n    if (is_dir($folder)){\n        echo '<a href=\"'.$folder.'/\">'.$folder.'</a><br>';\n    }\n}\n?>\n</body>\n</html>"
WWW_DIR = credentials.WWW_DIR
API_LIST = credentials.API_LIST
DEFICONF = credentials.DEFICONF
DEFID = credentials.DEFID

# program start
basicConfig(filename=logfile, format='%(asctime)s - %(message)s', level=INFO)
info("######################################")
info(f"Start {filename}")

errors = []

save_json_to_www(WWW_DIR, "systeminfo", get_systeminfo())
save_json_to_www(WWW_DIR, "version", get_version (DEFID))

rpc_connection = create_connection_rpc(read_deficonf(DEFICONF))

try:
    functions = api_calls(API_LIST)
except Exception as e:
    functions = False
    errors.append(f'api_calls() {str(e)}')
    print (f'api_calls() {str(e)}')

if functions:
    for i in functions:
        print (f'{i} {functions[i]}')
        info (f'{i} {functions[i]}')
        try:
            if   len(functions[i]) == 0:
                save_json_to_www(WWW_DIR, i, getattr(rpc_connection, i)())
            elif len(functions[i]) == 1:
                save_json_to_www(WWW_DIR, i, getattr(rpc_connection, i)(functions[i][0]))
            elif len(functions[i]) == 2:
                save_json_to_www(WWW_DIR, i, getattr(rpc_connection, i)(functions[i][0], functions[i][1]))
            elif len(functions[i]) == 3:
                save_json_to_www(WWW_DIR, i, getattr(rpc_connection, i)(functions[i][0], functions[i][1], functions[i][2]))
        except Exception as e:
            errors.append(f'{i} {str(e)}')
            print (f'{i} {str(e)}')

try:
    servername = gethostname()
    ip_address = gethostbyname(servername)
    print(f"IP address {ip_address} successfully collected for {servername}")
except Exception as e:
    errors.append(e)
    servername = None
    ip_address = None

print(f'removed directorys: {remove_unused_dirs(WWW_DIR, functions.keys() | {"systeminfo","version"})}')

if (errors):
    text = f"Problems with {filename} on {servername} {ip_address}\n{errors}"
    print (text)
    info(text)

info(f"End {filename}")
