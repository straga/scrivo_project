import asyncio
import machine
import os
import _thread
import gc


gc.threshold(4096)  # Garbage Collector, need test, may not need or some other value or disable

STOP = False  # Stop flag
storage_dir = "."  # Storage patch
# STACK THREAD
STACK_SIZE = 12 * 1024  # Stack size for ESP32
#STACK_SIZE = 12 * 1024  # Stack size for ESP32s2 or psram need test
TREAD = True  # Run in tread

# WDT
async def run_wdt():
    # import gc
    wdt = machine.WDT(timeout=30000)
    # wdt = machine.WDT(timeout=120000)
    # print("WDT: RUN")
    while True:
        wdt.feed()
        # gc.collect()
        # print(f"Free Mem: {gc.mem_free()}")
        # print("WDT RESET")
        await asyncio.sleep(5)


# VFS SIZE
def vfs():
    fs_stat = os.statvfs("/")
    fs_size = fs_stat[0] * fs_stat[2]
    fs_free = fs_stat[0] * fs_stat[3]
    print("File System Size {:,} - Free Space {:,}".format(fs_size, fs_free))


# Loader
async def loader():

    print(" ")
    print(" ")

    if STOP:
        print("Loader: stop")
        return

    # Partition name
    part_name = os.getcwd()
    print(f"Part Name: {part_name}")

    # Core
    from scrivo.core import Core
    Core(part_name=part_name)
    print("CORE: init")

    # Parse config file
    filename = 'board.yml'
    print("Parse Config: board.yml")
    try:
        from scrivo.module import parse_config
        await parse_config(filename)
    except Exception as e:
        print(f"ERROR: config file - {e}")


def main():
    # VFS info print
    vfs()

    # Create AsyncIO Tasks
    print("Create Event Tasks")
    asyncio.create_task(run_wdt())
    asyncio.create_task(loader())

    if TREAD:
        print("Start Event Loop in thread: NonBlock Repl")
        loop = asyncio.get_event_loop()
        _ = _thread.stack_size(STACK_SIZE)
        _thread.start_new_thread(loop.run_forever, ())
    else:
        print("Start Event Loop: Block Repl")
        loop = asyncio.get_event_loop()
        loop.run_forever()

    print("Main: Done")


if __name__ == "__main__":
    print("Import Safe")

    try:
        import safe
    except ImportError:
        print("Safe not found")
        pass

    # MAIN
    print("__main__")
    main()
