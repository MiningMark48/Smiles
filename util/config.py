import logging
import os.path as osp
import yaml

log = logging.getLogger("smiles")


class BotConfig:

    def __init__(self):
        self.config_path = "config.yml"
        self.def_config = {
            'bot': {
                'token': 'bot.token', 'key': '!', 'owners': []
            },
            'note': 'See demo_config.yml for more help on setting up this config!'
        }

        self.data = self.load_data()
        self.do_run = True

    def load_data(self):
        if osp.isfile(self.config_path):
            with open(self.config_path, 'r') as file:
                data = yaml.full_load(file)
                # Logger.info("Config loaded.")
                return data

        else:
            with open(self.config_path, 'w') as file:
                log.warn("Config file not found, creating...")
                yaml.dump(self.def_config, file)
                log.info("Config file created")
                self.do_run = False
                raise Exception("Config created, needs to be filled.")

    def get_api_key(self, name):
        try:
            result = self.data['api_keys'][name]
            if result:
                return result
        except KeyError:
            log.fatal(f"API key not found : {name}")
            return None
