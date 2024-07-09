# Avoid Rollback
try:
    from boot_cfg import avoid_rollback
    avoid_rollback()
    del(avoid_rollback)
except Exception as e:
    print(f"Rollback: {e}")

# Sys path add
try:
    from boot_cfg import sys_path_act
    sys_path_act()
    del(sys_path_act)
except Exception as e:
    print(f"sys path: {e}")


