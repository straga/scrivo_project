import asyncio
import gc
import json
from scrivo.core import Core
from scrivo.dev import DataClassArg
from scrivo.dev import secret

from scrivo import logging
log = logging.getLogger("CORE")
#log.setLevel(logging.DEBUG)


def import_module(module_name, configs):

    module = None
    sub_module = None
    print("  ")
    log.info(f"Load: {module_name}")
    #log.debug(f"  Configs: {configs}")
    mod_runnner = None
    try:
        # Split module name to module and sub module
        _module = module_name.split('_')
        if len(_module) == 2:
            module = _module[0]
            sub_module = _module[1]
        else:
            module = _module[0]

        log.info(f"  Module: {module} - Sub: {sub_module}")

        # Import module
        path_runner = f"scrivo_{module}._runner"
        mod_runnner = __import__(path_runner, None, None, ["_runner"], 0).Runner

    except Exception as e:
        log.error(f"  Mod Runner: {e}")

    # Run module if it's not None
    if mod_runnner is not None:
        core = Core.core()
        _runner = None
        try:
            _runner = core.env(module)
            log.info(f"  Runner: {module} - {_runner}")
            # If runner is not run before, create new runner. Use for multiple sub module
            if _runner is None:
                _runner = mod_runnner(name=f"scrivo_{module}", env=module)
                core.env.set(module, _runner)
            # Set configs to runner
            props = DataClassArg(sub=sub_module, configs=configs)
            log.info(f"  Activate: {module} {'' if sub_module is None else sub_module}")
            # Activate function
            _runner.activate(props)
        except Exception as e:
            log.error(f"  Import: {e}")

        log.info(f"  Import Done: {module}")
    gc.collect()
    #print(f"Ram Free: {gc.mem_free()}, usage: {gc.mem_alloc()}")

    try:
        import micropython
        micropython.mem_info()
    except Exception:
        pass


    log.info(f"Loaded: {module_name}")
    print("  ")


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


async def parse_config(filename):
    base_gruop = None
    current_group = None
    current_element = None
    elements = []

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
