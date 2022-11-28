"""

------------------------------------------------------------

        - Updater Script -    
    - by MiningMark48 (2021) -   
- Designed for Windows --> Linux -

------------------------------------------------------------

This script is used to update the bot.

This script may not work for you. This 
is here for me.

This may also not be the best method of 
updating, but it works, and if it ain't 
broke, don't fix it.

------------------------------------------------------------

"""

import argparse
import os
import socket
import time
from typing import List
import yaml
import pysftp as sftp
from ssh2.session import Session
from tqdm import tqdm


def main(config_path: str):
    load_config(config_path)

    upload_files(local_dirs, local_files)

    print("------------------")

    # Comment line below if using reloadall command
    # connect_and_start("tidalbot_python")

    print("------------------")

    print("Finished in {} seconds".format(str(time.time() - start_time)[:4]))

    print("------------------")


def load_config(config_path: str):
    with open(config_path, "r") as file:
        data = yaml.full_load(file)

        global remote_host
        global remote_user
        global remote_password
        global remote_path
        global remote_py_ver

        remote_data = data["remote"]
        remote_host = remote_data["host"]
        remote_user = remote_data["user"]
        remote_password = remote_data["password"]
        remote_path = remote_data["path"]
        remote_py_ver = remote_data["python_version"]

        global local_dirs
        global local_files

        local_data = data["local"]
        local_dirs = local_data["directories"]
        local_files = local_data["files"]

        print("Config file loaded.")


def get_def_pbar(iter_item):
    pbar = tqdm(iter_item, position=0, leave=True)
    return pbar


def put_r_portable(sftp, localdir, remotedir, preserve_mtime=False):
    os_entries = os.listdir(localdir)
    pbar = get_def_pbar(os_entries)
    index = 0
    for entry in pbar:
        remotepath = remotedir + "/" + entry
        localpath = os.path.join(localdir, entry)

        if not os.path.isfile(localpath):
            try:
                sftp.mkdir(remotepath)
            except OSError:
                pass
            put_r_portable(sftp, localpath, remotepath, preserve_mtime)
        else:
            if not localpath.endswith(".pyc"):
                pbar.set_description(f"Uploading {entry}")
                sftp.put(localpath, remotepath, preserve_mtime=preserve_mtime)
        index += 1


def upload_files(directories: list, files: list):
    print("Starting upload...")

    global remote_path

    cnopts = sftp.CnOpts()
    cnopts.hostkeys = None

    with sftp.Connection(host=remote_host, username=remote_user, password=remote_password, cnopts=cnopts) as s:
        print("Established SFTP connection")
        pbar = get_def_pbar(directories)
        for d in pbar:
            pbar.set_description(f"Uploading {d}")
            rem_path = f'{remote_path}/{d}'
            with s.cd(rem_path):
                put_r_portable(s, d, rem_path, preserve_mtime=False)
        with s.cd(rem_path):
            print("--")
            pbar = get_def_pbar(files)
            for f in pbar:
                pbar.set_description(f"Uploading {f}")
                s.put(f, f"{remote_path}/{f}", preserve_mtime=False)

    print("All uploads complete")
    s.close()
    print("Closed SFTP connection")


def connect_and_start(project_dir: str, install_req=False):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((remote_host, 22))
    print("Connected to socket")

    session = Session()
    session.handshake(sock)
    session.userauth_password(remote_user, remote_password)

    channel = session.open_session()
    print("Session opened")

    channel.shell()

    channel.write(f"cd {project_dir}\n")
    if install_req:
        channel.write(f"python{remote_py_ver} -m pip install -r requirements.txt\n")
    channel.write(f"nohup /usr/bin/python{remote_py_ver} bot.py &")

    print("Commands executed")
    time.sleep(1)

    channel.close()
    print(f"Exit status: {channel.get_exit_status()}")


if __name__ == "__main__":
    global start_time
    start_time = time.time()

    parser = argparse.ArgumentParser(description="Bot updater script via SSH")
    parser.add_argument("cfg_path", help="Path for the updater config file.")
    args = parser.parse_args()

    main(args.cfg_path)
