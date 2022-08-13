
import time
# AP
try:
    import network
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    time.sleep(1)
    ap.config(key="micro12345678", security=3)
except Exception as e:
    print(f"AP: {e}")

# WebRepl
try:
    import webrepl
    webrepl.start(password="micro")
except Exception as e:
    print(f"Webrepl: {e}")

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


