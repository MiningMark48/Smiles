import logging
import os
import zipfile
from datetime import datetime as dt
from os import listdir
from os import path
from os.path import isfile, join

from util.data.b2 import B2Backup
from util.config import BotConfig


log = logging.getLogger("smiles")


class DataBackups:
    def __init__(self):
        config = self.get_config()

        self.data_path = config["data_path"]
        self.backups_folder_name = config["backups_dir_name"]
        self.zip_name = config["zip_name"]
        self.b2_enabled = config["b2_enabled"]

    @staticmethod
    def get_config():
        return BotConfig().data["backups"]

    @staticmethod
    def get_subfolder_name():
        return str(dt.now().strftime('%m%d%y'))

    def backup_databases(self, always_run=True):
        subfolder_name = self.get_subfolder_name()

        if path.exists(f"{self.backups_folder_name}/{subfolder_name}/{self.zip_name}") and not always_run:
            return

        if not os.path.exists(f"{self.backups_folder_name}/{subfolder_name}"):
            os.makedirs(f"{self.backups_folder_name}/{subfolder_name}")

        loczip = f"{self.backups_folder_name}/{subfolder_name}/{self.zip_name}"
        zip = zipfile.ZipFile(loczip, "w", zipfile.ZIP_DEFLATED)

        only_files = [f for f in listdir(
            self.data_path) if isfile(join(self.data_path, f))]
        for f in only_files:
            self.backup_file(zip, f"{self.data_path}{f}")
            log.debug(f"File Backup | {f}")

        log.success(
            f"Backed up {len(only_files)} files to {self.backups_folder_name}/{subfolder_name}/{self.zip_name}")

        try:
            do_b2 = self.b2_enabled
        except KeyError:
            log.warn("B2 Backups disabled, skipping...")
        else:
            if do_b2:
                B2Backup().backup(loczip, self.zip_name, subfolder_name)
            else:
                log.warn("B2 Backups disabled, skipping...")

    def backup_file(self, zip, filename: str):
        folder_name = self.backups_folder_name
        subfolder_name = self.get_subfolder_name()
        # backup_loc = f"{folder_name}/{subfolder_name}/"
        # backup_name = f"{backup_loc}/{filename}"
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        if not os.path.exists(f"{folder_name}/{subfolder_name}"):
            os.makedirs(f"{folder_name}/{subfolder_name}")

        zip.write(filename, os.path.basename(filename))

        # log.debug(f"Backed up {filename} to {backup_loc}{self.zip_name}")
