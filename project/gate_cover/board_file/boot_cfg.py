
from esp32 import Partition


def avoid_rollback():
    # To avoid an automatic rollback at the next boot
    Partition.mark_app_valid_cancel_rollback()
    print("Avoid Rollback")


def sys_path_act():
    part_name = "root" # default folder for main
    #part_name = "dev"  # default folder for main
    # PARTITIONS // Path

    import sys
    import uos

    bootpart = Partition(Partition.BOOT)
    runningpart = Partition(Partition.RUNNING)

    print("INFO - Partitions")
    print(f"Boot:{bootpart}")
    print(f" Run:{runningpart}")


    # Can be use root folder as Partion Name.
    # part_info = runningpart.info()
    # part_name = part_info[4]

    try:
        uos.mkdir(part_name)
    except OSError as e:
        print(f"Path already exist: {e}")
        pass

    sys.path.append("/{}".format(part_name))
    sys.path.append("/{}/{}".format(part_name, "lib"))
    sys.path.append("/{}/{}".format(part_name, "module"))
    uos.chdir("/{}".format(part_name))

    print(f"Working Sys Path: {sys.path}")



