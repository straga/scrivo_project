
from time import sleep
import network

# Read secret file
def secret(search, default=False, path="./secret"):
    result = default
    try:
        with open(path) as f:
            for line in f:
                if line.startswith(search):
                    result = line.split(":")[-1].rstrip()
    except Exception as e:
        print(f"Error: secret file: {e}")
    return result

def find_strongest_network(sta, target_key):
    strongest_signal = None
    strongest_strength = float("-inf")

    for network in sta:
        try:
            print("scan: {}".format(network))
            ssid, _, _, signal_strength, _, _ = network
            if ssid.decode() == target_key and signal_strength > strongest_strength:
                strongest_signal = network
                strongest_strength = signal_strength
        except Exception as e:
            print("scan: {}".format(e))
            pass
    return strongest_signal

# Hostname
print("Hostname: Init")
hostname = secret("hostname")
try:
    if hostname:
        network.hostname(hostname)
except Exception as e:
    print(f"Hostname:err: {e}")
print(f"Hostname: {network.hostname()}")

# STA
print("STA: Init")
sta = network.WLAN(network.STA_IF)
sta.active(True)

# Scan networks
sta_scan = []
try:
    sta_scan = sta.scan()
except Exception as e:
    print("scan: {}".format(e))

# Connect to network
try:
    safe_wifi_ssid = secret("safe_wifi_ssid")
    safe_wifi_key = secret("safe_wifi_key")

    signal = find_strongest_network(sta_scan, safe_wifi_ssid)

    if signal:
        sta.connect(safe_wifi_ssid, safe_wifi_key)
        # sta.connect(safe_wifi_ssid, safe_wifi_key, bssid=signal[1])
        print("STA: wait 5 sec")
        # sleep(5)

    # check 5 time if connected break for
    for i in range(5):
        sta_conect = sta.isconnected()
        if sta_conect:
            break

        print(f" Wait STA: {i}\r", end="")
        sleep(1)

    print(f"STA: {sta.ifconfig()}")
    print("STA running on channel:", sta.config("channel"))

except Exception as e:
    print(f"STA: {e}")

# AP

try:
    # ap ssid
    ssid = secret("ap_ssid")
    if ssid:
        print("AP: Init")
        ap_conf = {"ssid": ssid, "key": "micro12345678", "security": 3}

        ap = network.WLAN(network.AP_IF)
        ap.active(True)

        sleep(1)

        key = secret("ap_key")
        if key and len(key) >= 8:
            ap_conf["key"] = key

        # ap channel
        channel = secret("ap_channel")
        if channel:
            ap_conf["channel"] = int(channel)

        print(f"AP: {ap_conf}")
        ap.config(**ap_conf)
        print("AP running on channel:", ap.config("channel"))

except Exception as e:
    print(f"AP:err: {e}")



# Telnet
print(f"Telnet: Init:")
try:
    import utelnetserver
    utelnetserver.start()
except Exception as e:
    print(f"Telnet: {e}")

# FTP
try:
    ftp = secret("safe_ftp")
    print(f"FTP: Init: {ftp}")
    if ftp:
        import uftpd
except Exception as e:
    print(f"FTP: {e}")



# Safe sleep
safe_sleep = int(secret("safe_sleep", 1))

print(" ")
print(" ")

for i_n in range(safe_sleep):
    # print wait in same line
    print(f" Wait safe: {safe_sleep - i_n}\r", end="")
    sleep(1)
