import platform
from os import path, makedirs, listdir
import re
from json import JSONEncoder, dumps
from socket import gethostbyname, gethostname
from decimal import Decimal
from subprocess import check_output
import shutil
from psutil import virtual_memory, cpu_percent, cpu_freq, net_io_counters  #pip install psutil
from psutil import cpu_count, disk_usage, disk_partitions #pip install psutil
from requests import get #pip install requests
from requests.auth import HTTPBasicAuth
from collections import OrderedDict
import configparser

API_INDEX_PHP = "<?PHP header('Content-Type: application/json');\n"\
                "\n$data = file_get_contents('data.json');\n"\
                "\necho $data;\n\n?>"
GLOBAL_INDEX_PHP =  "<!DOCTYPE html>\n<html>\n<body>\n<?PHP\n$verzeichnis = '.';\n"\
                    "$verz_inhalt = scandir($verzeichnis);\nforeach ($verz_inhalt as $folder)"\
                    "{\n    if (is_dir($folder)){\n        echo '<a href=\"'.$folder.'/\">'.$folder.'</a><br>';\n"\
                    "}\n}\n?>\n</body>\n</html>"

class DecimalEncoder (JSONEncoder):
    def default (self, obj):
        if isinstance (obj, Decimal):
            return float (obj)
        return JSONEncoder.default (self, obj)

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

def get_operators(filename):
    file = open(filename,'r')
    regex_pattern = r'masternode_operator\s*=\s*([A-HJ-NP-Za-km-z1-9]{34})'
    operatorlist = re.findall(regex_pattern, file.read())
    return operatorlist

def get_systeminfo():
    stats_data = {"disk_total": 0, "disk_used": 0, "disk_free": 0}
    partitions = disk_partitions()
    for i in enumerate(partitions):
        try:
            space = disk_usage(partitions[i[0]].mountpoint)
            stats_data["disk_total"] += space.total
            stats_data["disk_used"] += space.used
            stats_data["disk_free"] += space.free
        except Exception:
            continue

    stats_data["bytes_sent"]   = net_io_counters().bytes_sent
    stats_data["bytes_recv"]   = net_io_counters().bytes_recv
    stats_data["cpu_count"]    = cpu_count()
    stats_data["cpu_freq"]     = cpu_freq().current
    stats_data["cpu_load"]     = cpu_percent(interval=1, percpu=False)
    stats_data["memory_total"] = virtual_memory().total
    stats_data["memory_used"]  = virtual_memory().used
    stats_data["memory_free"]  = virtual_memory().free

    pName = platform.uname().system

    if "darwin" in pName.lower():
        pName = "macOS"

    # System Informationen
    stats_data["os"] = pName
    stats_data["osVersion"] = platform.uname().release
    stats_data["osArch"] = platform.uname().machine

    stats_data["python"] = ".".join(platform.python_version_tuple())
    try:
        stats_data["distri"] = platform.freedesktop_os_release()["PRETTY_NAME"]
    except:
        pass

    print (stats_data)
    return stats_data

def get_version(file):
    version = check_output([file, '--version'], encoding='UTF-8').split('\n', maxsplit=1)[0]
    print (version)
    return version

def get_servername():
    try:
        servername = gethostname()
        ip_address = gethostbyname(servername)
        print(f"IP address {ip_address} successfully collected for {servername}")
        return servername, ip_address
    except Exception:
        return "",""


def api_calls(filename):
    returnvalue = {}
    with open(filename) as file:
        for line in file.read().split('\n'):
            if line.startswith("=") or line.startswith("#"): #if header or commented, then skip
                continue
            if line:
                returnvalue[line.split(" ")[0]] = list(map(eval,line.split(" ")[1:]))
    return returnvalue

def remove_unused_dirs(folder, keep_dir):
    deleted = []
    for file in listdir(folder):
        if path.isdir(folder + "/" + file):
            if file.split("/")[-1] not in keep_dir:
                try:
                    shutil.rmtree(folder + "/" + file)
                    deleted.append(file)
                except OSError as err:
                    print(err)
                else:
                    print(f"The directory {file} is deleted successfully")
    return deleted

def get_serverlist_txt(filename):
    returnvalue = []
    with open(filename) as f:
        for i in f.read().split('\n'):
            infos = i.split(" ")
            
            if   len(infos) >= 3:
                returnvalue.append({"host": infos[0], "user": infos[1], "pwd": infos[2]})
            elif len(infos) == 2:
                returnvalue.append({"host": infos[0], "user": infos[1], "pwd": False})
            elif len(infos) == 1 and infos[0] != "":
                returnvalue.append({"host": infos[0], "user": False,    "pwd": False})
    return returnvalue

def get_mininginfo(server, errorlist):
    try:
        response = get(server["host"]+"getmininginfo", auth=HTTPBasicAuth(server["user"], server["pwd"]))
        if response.status_code == 200:
            return response.json()
        else:
            errorlist.append(server)
            return {}
    except Exception as err:
        errorlist.append(server)
        return {}

def get_operatorlist_txt(filename):
    returnvalue = []
    try:
        with open(filename) as f:
            for i in f.read().split('\n'):
                returnvalue.append(i)
    except Exception as err:
        print (err)
        
    return returnvalue

def add_operator_to_list(file, operator):
    fileobject = open(file, 'a')
    fileobject.write(operator+"\n")
    fileobject.close()

def zerodivision(n, d):
    return n / d if d else 0

# Problem with defi.conf, there are multiple entrys for masternode_operator possible
# Solution: https://stackoverflow.com/questions/15848674/how-to-configparse-a-file-keeping-multiple-values-for-identical-keys
class MultiOrderedDict(OrderedDict):
    def __setitem__(self, key, value):
        if key in self:
            if isinstance(value, list):
                self[key].extend(value)
                return
            elif isinstance(value,str):
                if len(self[key])>1:
                    return
        super(MultiOrderedDict, self).__setitem__(key, value)

def read_config_file(filename):
    # Problem with defi.conf, there are entrys without [section] -> workaround integrate a section [topsection]
    # Source: https://stackoverflow.com/questions/2885190/using-configparser-to-read-a-file-without-section-name
    config_parser = configparser.RawConfigParser(dict_type=MultiOrderedDict, strict=False)
    with open(filename) as file:
        config_parser.read_string(re.sub("\n\n*", "\n", "[topsection]\n" + file.read()))
    return config_parser

def get_credentials_from_config(config, network="main"):
    if (type(config) == type(configparser.RawConfigParser())):
        pass
        # config is already configparser class
    elif (type(config) == type("c:/tempfile")):
        # config is string, probably filename -> read config file
        config = read_config_file(config)
    else:
        raise ValueError(f"incopatible input type {type(config)}")

    if network in config:
        if "rpcuser" in config[network]:
            rpcuser = config[network]["rpcuser"]
        elif "rpcuser" in config["topsection"]:
            rpcuser = config["topsection"]["rpcuser"]
        else:
            rpcuser = False

        if "rpcpassword" in config[network]:
            rpcpass = config[network]["rpcpassword"]
        elif "rpcpassword" in config["topsection"]:
            rpcpass = config["topsection"]["rpcpassword"]
        else:
            rpcpass = False

        if "rpcbind" in config[network]:
            rpcbind = config[network]["rpcbind"]
        elif "rpcbind" in config["topsection"]:
            rpcbind = config["topsection"]["rpcbind"]
        else:
            rpcbind = False

        if "rpcport" in config[network]:
            rpcport = config[network]["rpcport"]
        elif "rpcport" in config["topsection"]:
            rpcport = config["topsection"]["rpcport"]
        else:
            rpcport = False

    else:
        if "rpcuser" in config["topsection"]:
            rpcuser = config["topsection"]["rpcuser"]
        elif "rpcuser" in config["main"]:
            rpcuser = config["main"]["rpcuser"]
        elif "rpcuser" in config["test"]:
            rpcuser = config["test"]["rpcuser"]
        else:
            rpcuser = False

        if "rpcpassword" in config["topsection"]:
            rpcpass = config["topsection"]["rpcpassword"]
        elif "rpcpassword" in config["main"]:
            rpcpass = config["main"]["rpcpassword"]
        elif "rpcpassword" in config["test"]:
            rpcpass = config["test"]["rpcpassword"]
        else:
            rpcpass = False

        if "rpcbind" in config["topsection"]:
            rpcbind = config["topsection"]["rpcbind"]
        elif "rpcbind" in config["main"]:
            rpcbind = config["main"]["rpcbind"]
        elif "rpcbind" in config["test"]:
            rpcbind = config["test"]["rpcbind"]
        else:
            rpcbind = False

        if "rpcport" in config["topsection"]:
            rpcport = config["topsection"]["rpcport"]
        elif "rpcport" in config["main"]:
            rpcport = config["main"]["rpcport"]
        elif "rpcbind" in config["test"]:
            rpcport = config["test"]["rpcbind"]
        else:
            rpcport = False

    return {"rpcuser": rpcuser,
            "rpcpass": rpcpass,
            "rpcbind": rpcbind,
            "rpcport": rpcport}
