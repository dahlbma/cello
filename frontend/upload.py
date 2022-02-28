import sys, os, platform, dbInterface

if (len(sys.argv) == 2) or (len(sys.argv) == 3):
    # only executable
    os_name = platform.system()
    exec_path = f"{sys.argv[1]}"
    if os.path.isfile(exec_path):
        with open(exec_path, 'rb') as f:
            try:
                r, status = dbInterface.uploadBinary(os_name, f)
                if not status:
                    raise Exception
            except:
                print("Upload failed.")
                quit()
            print("Upload successful.")
    if len(sys.argv) == 3:
        ver_no = f"sys.argv[2]"
        if os.path.isfilever_dat_path():
            try:
                r, status = dbInterface.uploadVersionNo(ver_no)
            except:
                print("Version number update failed.")
                quit()
            print("Version number update successful.")
    quit()

print("Incorrect number of arguments.")
print("Please specify path(s) to executable and/or ver.dat")
print("like: python upload.py <exec_path> <ver.dat_path>")