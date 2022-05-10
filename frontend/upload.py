import sys, os, platform, dbInterface, json, argparse
import getpass

def upload(target, version, launcher):
    # prompt login
    username = input("Username: ")
    password = getpass.getpass("Password: ")
    login_response = None
    try:
        login_response = dbInterface.login(username, password, "Live")
        if login_response.status_code != 200:
            raise Exception
    except:
        print(f"Login failed with code {login_response.status_code}. Exitting.")
        return
    token = login_response.content
    os_name = platform.system()
    if target != None:
        exec_path = target
        if os.path.isfile(exec_path):
            with open(exec_path, 'rb') as f:
                try:
                    r, status = dbInterface.uploadBinary(token, os_name, f)
                    if not status:
                        raise Exception
                    print("Main upload successful.")
                except:
                    print("Main upload failed.")
        else:
            print(f"file '{exec_path}' not found!")
    if version != None:
        ver_path = version
        if os.path.isfile(ver_path):
            with open(ver_path, "r") as ver_file:
                data = json.load(ver_file)
                ver_no = data["version"]
                try:
                    r, status = dbInterface.uploadVersionNo(token, ver_no)
                    if not status:
                        raise Exception
                    print("Version number update successful.")
                except:
                    print("Version number update failed.")
        else:
            print(f"file '{ver_path}' not found!")
    if launcher != None:
        lau_path = launcher
        if os.path.isfile(lau_path):
            with open(lau_path, 'rb') as f:
                try:
                    r, status = dbInterface.uploadLauncher(token, os_name, f)
                    if not status:
                        raise Exception
                    print("Launcher upload successful.")
                except:
                    print("Launcher upload failed.")
        else:
            print(f"file '{lau_path}' not found!")

parser = argparse.ArgumentParser()
parser.add_argument('-t', action="store", dest="target", type=str, default=None)
parser.add_argument('-v', action="store", dest="version", type=str, default=None)
parser.add_argument('-l', action="store", dest="launcher", type=str, default=None)

res = parser.parse_args()

if (res.target == None) and (res.version == None) and (res.launcher == None):
    #help message
    print("Please specify path(s) to executables and/or version data files")
    print("-t <path>: path to main executable")
    print("-v <path>: path to version data file")
    print("-l <path>: path to launcher executable")
else:
    upload(res.target, res.version, res.launcher)
