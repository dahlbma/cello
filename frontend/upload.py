import sys, os, platform, dbInterface, json
import getpass

if (len(sys.argv) == 2) or (len(sys.argv) == 3):
    
    # prompt login
    username = input("Username: ")
    password = getpass.getpass("Password: ")
    login_response = None
    try:
        login_response = dbInterface.login(username, password, "Live")
        if login_response.status_code != 200:
            raise Exception
    except:
        print("Incorrect credentials. Exitting.")
        sys.exit()
    token = login_response.content
    os_name = platform.system()
    exec_path = f"{sys.argv[1]}"
    if os.path.isfile(exec_path):
        with open(exec_path, 'rb') as f:
            try:
                r, status = dbInterface.uploadBinary(token, os_name, f)
                if not status:
                    raise Exception
            except:
                print("Upload failed.")
                sys.exit()
            print("Upload successful.")
    if len(sys.argv) == 3:
        ver_path = f"{sys.argv[2]}"
        if os.path.isfile(ver_path):
            with open(ver_path, "r") as ver_file:
                data = json.load(ver_file)
                ver_no = data["version"]
                try:
                    r, status = dbInterface.uploadVersionNo(token, ver_no)
                    if not status:
                        raise Exception
                except:
                    print("Version number update failed.")
                    sys.exit()
            print("Version number update successful.")
    sys.exit()

print("Incorrect number of arguments.")
print("Please specify path(s) to executable and/or ver.dat")
print("like: python upload.py <exec_path> <ver.dat_path>")