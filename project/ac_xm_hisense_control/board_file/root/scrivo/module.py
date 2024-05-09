import asyncio
import gc
import json
from scrivo.core import Core
from scrivo.dev import DataClassArg
from scrivo.dev import secret

from scrivo import logging
log = logging.getLogger("CORE")
log.setLevel(logging.DEBUG)


class Module:

    def __init__(self, name, env):
        self.name = env
        self.core = Core.core()
        self.mbus = self.core.mbus
        log.info(f"Module: {name}")

    # def __call__(self, *args, **kwargs):
    #     # This method will be called when an instance of this class is "called" like a function.
    #     pass

    # Humanize sub to topic
    def sub_h(self, topic, func):
        return self.mbus.sub_h(topic=topic, env=self.name, func=func)

    def activate(self, props):
        log.info(f"Base Module Activate")

    # # use for notify to mbus from other module? need defain what will be send
    # def notify(self):
    #     pass


def import_module(module_name, configs):

    module = None
    sub_module = None
    print("  ")
    log.info(f"Load: {module_name}")

    # log.debug(f"  Configs: {configs}")

    mod_runnner = None
    try:
        _module = module_name.split('_')

        if len(_module) == 2:
            module = _module[0]
            sub_module = _module[1]
        else:
            module = _module[0]

        log.info(f"  Module: {module} - Sub: {sub_module}")

        path_runner = f"scrivo_{module}._runner"
        mod_runnner = __import__(path_runner, None, None, ["_runner"], 0).Runner


    # mod_runnner = __import__("scrivo_board", None, None, ["_runner"], 0).Runner
    except Exception as e:
        log.error(f"  Mod Runner: {e}")

    if mod_runnner is not None:

        # log.info(f"  mod_runnner: {mod_runnner}")
        core = Core.core()

        _runner = None
        try:
            _runner = core.env(module)
            log.info(f"  Runner: {module} - {_runner}")
            if _runner is None:
                _runner = mod_runnner(name=f"scrivo_{module}", env=module)
                core.env.set(module, _runner)
            props = DataClassArg(sub=sub_module, configs=configs)
            log.info(f"  Activate: {module} {'' if sub_module is None else sub_module}")
            #check if activate method is async
            _runner.activate(props)
        except Exception as e:
            log.error(f"  Import: {e}")

        log.info(f"  Import Done: {module}")
    print("  ")


async def parse_config(filename):
    base_gruop = None
    current_group = None
    current_element = None
    elements = []

    def deserialize_value(value):
        # Remove leading and trailing whitespaces
        value = value.strip()

        # Try to convert to int
        try:
            return int(value)
        except ValueError:
            pass

        # Try to convert to float
        try:
            return float(value)
        except ValueError:
            pass

        # Try to parse list
        if value.startswith('[') and value.endswith(']'):
            try:
                return json.loads(value)
            except ValueError:
                pass

        # Try to convert to bool
        if value.lower() == 'true':
            return True
        elif value.lower() == 'false':
            return False

        # It's a string, remove extra quotes if they exist
        if value.startswith('"') and value.endswith('"'):
            return value[1:-1]
        elif value.startswith("'") and value.endswith("'"):
            return value[1:-1]

        return value

    with open(filename, 'r') as file:
        for line in file:  # read file line by line
            line = line.strip('\n')
            if line.startswith('#'):  # ignore comment lines
                continue

            if not line.strip().startswith('- ') and line.endswith(':'):  # check if line starts a group

                if current_group is not None and elements:  # if a group was being parsed, load module
                    import_module(current_group, elements)
                    await asyncio.sleep(0.1)

                if line.startswith('  '):
                    current_group = f"{base_gruop}_{line.strip()[:-1]}"
                else:
                    base_gruop = line.strip()[:-1]  # remove the colon at the end
                    current_group = base_gruop

                elements = []
                current_element = None

            elif line.strip().startswith('- '):  # check if line starts an element
                line = line.strip()
                key, value = line[2:].split(':')
                # log.debug(f"  key: {key} - value: {value} - secret: {value.strip().startswith('!secret ')}")
                if value.strip().startswith('!secret '):
                    secret_key = value.strip()
                    value = secret(secret_key)
                    # log.debug(f"    Secret: {value}")
                    # log.debug(f"    Secret: {value}")
                if value:
                    current_element = {key.strip(): deserialize_value(value)}
                    elements.append(current_element)
                else:
                    log.info(f"  Wrong secret: {line}")

            elif current_element is not None and ':' in line:  # ensure line contains a colon
                line = line.strip()
                key, value = line.split(':', 1)
                # log.debug(f"  key: {key} - value: {value} - secret: {value.strip().startswith('!secret ')}")
                if value.strip().startswith('!secret '):
                    secret_key = value.strip()
                    value = secret(secret_key)
                    # log.debug(f"    Secret: {value}")
                if value:
                    current_element[key.strip()] = deserialize_value(value.strip())
                else:
                    log.info(f"  Wrong secret: {line}")

        # Load Module after the end of the file
        if current_group is not None:
            import_module(current_group, elements)
            await asyncio.sleep(0.1)
