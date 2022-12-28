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


# noinspection PyUnresolvedReferences
class DataBackups:
    def __init__(self):
        config = self.get_config()

        self.data_path = config["data_path"]
        self.backups_folder_name = config["backups_dir_name"]
        self.zip_name = config["zip_name"]
        self.b2_enabled = config["b2_enabled"]

        split_zip_name = str(self.zip_name).split(".")
        self.zip_name = f"{split_zip_name[0]}_{self.get_zip_ext()}.{split_zip_name[1]}"

    @staticmethod
    def get_config():
        return BotConfig().data["backups"]

    @staticmethod
    def get_subfolder_name():
        return str(dt.now().strftime('%m%d%y'))

    @staticmethod
    def get_zip_ext():
        return str(dt.now().strftime('%H%M'))

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

        skipped = 0
        for f in only_files:
            if f.startswith("_"):   # Skip backup on any files that start with '_' (Dev purposes)
                skipped += 1
                continue
            self.backup_file(zip, f"{self.data_path}{f}")
            log.debug(f"File Backup | {f}")

        log.info(
            f"Backed up {len(only_files) - skipped} files to {self.backups_folder_name}/{subfolder_name}/{self.zip_name}")

        log.success("Backup complete.")

        try:
            do_b2 = self.b2_enabled
        except KeyError:
            log.warn("Unable to pull from config. Assuming B2 Backups are disabled, skipping...")
        else:
            if do_b2:
                B2Backup().backup(loczip, self.zip_name, subfolder_name)
            else:
                log.info("B2 Backups disabled, skipping...")

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
