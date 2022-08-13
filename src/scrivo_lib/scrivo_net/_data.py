
schema = '''
    {
      "sta_cfg": {
        "_schema" : "_schema",
        "name": "wifi_sta_cfg",
        "sch": [
            ["name", ["str",""] ],
            ["ssid", ["str", ""] ],
            ["key", ["str", ""]],
            ["active", ["bool", true]]
        ]
      },
    
      "ap_cfg": {
        "_schema" : "_schema",
        "name": "wifi_ap_cfg",
        "sch": [
            ["name", ["str",""] ],
            ["ssid", ["str", ""] ],
            ["channel", ["int", 11]],
            ["hidden", ["bool", false]],
            ["key", ["str", ""]],
            ["security", ["int", 3]],
            ["delay", ["int", 360]],
            ["active", ["bool", true]],
            ["espnow", ["bool", false]],
            ["protocol", ["int", -1]]
        ]
      },
    
      "scan_cfg": {
        "_schema" : "_schema",
        "name": "wifi_scan_map",
        "sch": [
            ["name", ["str",""] ],
            ["ssid", ["str", ""] ],
            ["bssid", ["str", ""]],
            ["RSSI", ["int", 0]],
            ["channel", ["int", 0]],
            ["security", ["int", 0]],
            ["hidden", ["int", 0]]
        ]
      }
    }
    '''

depend = ["board"]
data = None



