from os import path, makedirs, listdir
from json import JSONEncoder, dumps
from logging import basicConfig, info, INFO
from decimal import Decimal
from bitcoinrpc.authproxy import AuthServiceProxy
from requests import get
from socket import gethostbyname, gethostname
from psutil import virtual_memory, cpu_percent, cpu_freq, net_io_counters, cpu_count, disk_usage, disk_partitions
import credentials
import shutil

# psutil, python-bitcoinrpc, requests nicht Standardinstallation

class DecimalEncoder (JSONEncoder):
    def default (self, obj):
        if isinstance (obj, Decimal):
            return float (obj)
        return JSONEncoder.default (self, obj)

filename = path.basename(__file__)
directory = path.dirname(__file__)
logfile = path.dirname(__file__)+"/"+filename.split(".")[0]+".log"

standard_php_file = "<?PHP header('Content-Type: application/json');\n\n$data = file_get_contents('data.json');\n\necho $data;\n\n?>"
www_directory = "c:/temp/www"
API_LIST = "C:/Temp/api_collector/api_calls.txt"
errors = []

basicConfig(filename=logfile, format='%(asctime)s - %(message)s', level=INFO)
info("######################################")
info(f"Start {filename}")

def save_json_to_www(subfolder,data):

    if not path.exists(www_directory+"/"+subfolder):
        makedirs(www_directory+"/"+subfolder)
        phpfileobject = open(www_directory+"/"+subfolder+"/index.php", 'w')
        phpfileobject.write(standard_php_file)
        phpfileobject.close()
        #TODO 1 create empty data file
        #TODO 2 set chmod rights
        #TODO 3 set owner chown for new directory and file www-data
        #TODO 4 update global index.php help/linkfile with new directory

    json_data = dumps(data, cls = DecimalEncoder, sort_keys=True, indent=4)
    fileobject = open(www_directory+"/"+subfolder+"/data.json", 'w')
    fileobject.write(json_data)
    fileobject.close()
    return 0

def create_connection_rpc(cred):
    url = "http://%s:%s@%s:%s/"%(cred.rpc_username, cred.rpc_password, cred.rpc_hostname, cred.rpc_port)
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

def remove_unused_dirs(keep_dir):
    deleted = []
    for file in listdir(www_directory):
        if path.isdir(www_directory + "/" + file):
            if file.split("/")[-1] not in keep_dir:
                try:
                    shutil.rmtree(www_directory + "/" + file)
                    deleted.append(file)
                except OSError as e:
                    print(e)
                else:
                    info(f"The directory {file} is deleted successfully")
    return deleted

def get_space_sum():
    partitions = disk_partitions()
    total = free = used = 0
    for i in enumerate(partitions):
        try:
            space = disk_usage(partitions[i[0]].mountpoint)
            total += space.total
            free += space.free
            used += space.used
        except:
            continue
    return {"disk_total": total, "disk_used": used, "disk_free": free}

stats_data = {}
stats_data["bytes_sent"]   = net_io_counters().bytes_sent
stats_data["bytes_recv"]   = net_io_counters().bytes_recv
stats_data["cpu_count"]    = cpu_count()
stats_data["cpu_freq"]     = cpu_freq().current
stats_data["cpu_load"]     = cpu_percent(interval=1, percpu=False)
stats_data["memory_total"] = virtual_memory().total
stats_data["memory_used"]  = virtual_memory().used
stats_data["memory_free"]  = virtual_memory().free
stats_data |= get_space_sum()
info (stats_data)
save_json_to_www("systeminfo", stats_data)

rpc_connection = create_connection_rpc(credentials)
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
                save_json_to_www(i, getattr(rpc_connection, i)())
            elif len(functions[i]) == 1:
                save_json_to_www(i, getattr(rpc_connection, i)(functions[i][0]))
            elif len(functions[i]) == 2:
                save_json_to_www(i, getattr(rpc_connection, i)(functions[i][0], functions[i][1]))
            elif len(functions[i]) == 3:
                save_json_to_www(i, getattr(rpc_connection, i)(functions[i][0], functions[i][1], functions[i][2]))
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

print(f'removed directorys: {remove_unused_dirs(functions.keys() | {"systeminfo"})}')

if (errors):
    text = f"Problems with {filename} on {servername} {ip_address}\n{errors}"
    print (text)
    info(text)
#    get(f'https://api.telegram.org/{credentials.telegram_token}/sendMessage?chat_id={credentials.telegram_chatid}&text={text}')

info(f"End {filename}")
