
import uasyncio as asyncio
import machine
import uos
import _thread
import gc
from time import sleep

try:
    from scrivo import logging
    log = logging.getLogger('MAIN')
    logging.basicConfig(level=logging.INFO)
except Exception as e:
    print(f"Error: {e}")


storage_dir = "."  # Storage patch

# WDT
async def run_wdt():
    import gc
    wdt = machine.WDT(timeout=30000)
    #wdt = machine.WDT(timeout=120000)
    log.info("WDT: RUN")
    while True:
        wdt.feed()
        gc.collect()
        # print("WDT RESET")
        await asyncio.sleep(5)


# Core
def core():
    from scrivo.core import Core
    from scrivo.mbus.mbus import MbusManager
    from scrivo.config.config import ConfigManager

    part_name = uos.getcwd()
    log.info(f"Part Name: {part_name}")

    # VFS SIZE
    fs_stat = uos.statvfs('/')
    fs_size = fs_stat[0] * fs_stat[2]
    fs_free = fs_stat[0] * fs_stat[3]
    log.info("File System Size {:,} - Free Space {:,}".format(fs_size, fs_free))

    # MBUS
    log.info("MBUS: init")
    _mbus = MbusManager()

    # CONF
    log.info("CONF: init")
    _conf = ConfigManager("{}/u_config".format(storage_dir))

    # CORE
    log.info("CORE: init")
    _core = Core(_mbus, _conf)
    _core.part_name = part_name
    _core.storage_dir = storage_dir

    return "Done"


# Loader
async def loader():

    # use for debug : webrepl connect.
    try:
        safe_sleep = secret("!secret safe_sleep", "0.1")
        log.info(f"Wait: {safe_sleep} safe_sleep")
        await asyncio.sleep(float(safe_sleep))
    except Exception as e:
        log.error(f"Error: {e}")

    # LOADER
    from scrivo.loader.loader import Loader
    log.info("Module: Init")

    try:
        _umod = Loader(["board", "net"])
    except Exception as e:
        log.info(f"Module: Load: {e}")
        _umod = Loader()

    log.info("Module: List")
    await _umod.module_list()

    log.info("Module: Act")
    await _umod.module_act()

    unload_module('scrivo.loader')
    unload_module('boot_cfg')
    gc.collect()


def unload_module(mod_name):
    # removes module from the system
    import sys
    if mod_name in sys.modules:
        del sys.modules[mod_name]

def main():

    log.info("2.step: Init Scrivo Core")
    core()

    log.info("3.step: Create Event Tasks")
    asyncio.create_task(run_wdt())
    asyncio.create_task(loader())

    # print("3.step: Start Event Loop: Block Repl")
    # loop = asyncio.get_event_loop()
    # loop.run_forever()

    # # AsyncIO in thread
    log.info("0.step: Start Event Loop in thread: NonBlock Repl")
    loop = asyncio.get_event_loop()
    _ = _thread.stack_size(8 * 1024)
    _thread.start_new_thread(loop.run_forever, ())

    log.info("4.step: Done Main")

    # Add debug message for "select" module
    # log_debug = logging.getLogger("SWITCH")
    # log_debug.setLevel(logging.DEBUG)

def secret(val, default=False, _secret="!secret "):
    if isinstance(val, str) and val.startswith(_secret):
        search = val.split(_secret, 1)[-1]
        result = default
        try:
            with open("./secret") as f:
                for line in f:
                    if line.startswith(search):
                        result = line.split(":")[-1].rstrip()
        except Exception as e:
            log.error(f"Error: secret file: {e}")
    return result

if __name__ == '__main__':

    print("1.Network")
    import network

    safe_wifi_ssid = secret("!secret safe_wifi_ssid")
    safe_wifi_pwd = secret("!secret safe_wifi_pwd")

    if safe_wifi_ssid and safe_wifi_pwd:
        sta = network.WLAN(network.STA_IF)
        sta.active(True)
        sta.connect(safe_wifi_ssid, safe_wifi_pwd)
        sleep(5)
        print(f"STA: {sta.ifconfig()}")
    print("FTP: Init")
    try:
        import uftpd
    except Exception as e:
        print(f"FTP: {e}")

    print("__main__")
    main()



