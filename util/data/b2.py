from util.config import BotConfig
import logging
from b2sdk.v1 import B2Api, InMemoryAccountInfo


log = logging.getLogger("tidalbot")


class B2Backup:
    def __init__(self):

        self.data = self.get_config()

    @staticmethod
    def get_config():
        return BotConfig().data["backups"]["b2_info"]

    def backup(self, file_loc, file_name, folder_name):

        if not self.data:
            log.warn("Not backing up to B2, config not found.")
            return

        log.info("Connecting to B2...")

        try:
            info = InMemoryAccountInfo()
            b2_api = B2Api(info)
            application_key_id = self.data["app_key"]["id"]
            application_key = self.data["app_key"]["key"]
            b2_api.authorize_account(
                "production", application_key_id, application_key)
            bucket_name = self.data["bucket"]["name"]
            bucket = b2_api.get_bucket_by_name(bucket_name)
        except Exception as e:
            log.fatal(f"Connection to B2 failed : \n\t{e}")
        else:
            log.info("Connected to B2")

            log.info("Starting backup upload to B2...")
            bucket.upload_local_file(
                local_file=file_loc,
                file_name=f"{self.data['bucket']['backup_folder_name']}/{folder_name}/{file_name}",
                file_infos={"how": "automated"},
            )

            log.success("Upload to B2 complete.")
