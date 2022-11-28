import os.path as osp
import yaml
import logging


log = logging.getLogger("tidalbot")


features_path = "features.yml"

def get_extensions() -> list:
    """
    Gets extensions from the `features.yml`
    to be loaded into the bot

    :return: list
    """

    log.info("Getting extensions...")

    exts = []

    if osp.isfile(features_path):
        with open(features_path, 'r') as file:
            data = yaml.full_load(file)

            extensions = data["extensions"]
            
            for e in extensions:
                e_name = e["extension"]

                if "directory" in e:
                    e_name = f"{e['directory']}.{e_name}"
                
                e_enabled = e["enabled"] if "enabled" in e else True
                if e_enabled:
                    e_external = e["external"] if "external" in e else False
                    
                    if e_external:
                        exts.append(e_name)
                        log.debug(f"Extension Found | External | {e_name}")
                    else:
                        exts.append(f"cogs.{e_name}")
                        log.debug(f"Extension Found | Internal | {e_name}")
                    
                    # else:
                    #     exts.append(f"cogs.{category}.{e_name}")
                    #     log.debug(f"Extension Found | Cog | {category}.{e_name}")

    log.info(f"Found *{len(exts)}* extensions.")
    # log.debug(exts)

    return exts

def get_commands_blacklist() -> list:
    """
    Get commands from `features.yml` to blacklist,
    preventing them from being added to the bot

    :returns: list
    """

    log.info("Getting commands blacklist...")

    cmds = []

    if osp.isfile(features_path):
        with open(features_path, 'r') as file:
            data = yaml.full_load(file)

            if not "commands" in data:
                log.warn("Commands blacklist object not found in features.yml file")
                return list() # Return empty list

            commands = data["commands"]

            if not commands or len(commands) == 0:
                log.debug("Empty blacklist commands data, returning...")
                return list() # Return empty list
            
            for c in commands:
                c_name = c["command"]
                
                e_enabled = c["enabled"] if "enabled" in c else True
                if not e_enabled:
                    cmds.append(c_name)
                    log.debug(f"Command Found | Blacklist | {c_name}")

    log.info(f"Found *{len(cmds)}* commands to blacklist.")

    return cmds
