
schema = '''
    {
      "mqtt_cfg": {
        "_schema" : "_schema",
        "name": "mqtt_cfg",
        "sch": [
            ["name",   ["str","default"] ],
            ["addr",   ["str", "25"] ],
            ["port",   ["int", 1883]],
            ["seq",    ["int", 10]],
            ["user",   ["str", null] ],
            ["pwd",    ["str", null] ],
            ["lwt",    ["bool", true] ],
            ["birth",  ["bool", true] ],
            ["active", ["bool", true]],
            ["sub", ["list", [] ] ]
        ]
      }
    }
'''
data = None
depend = ["net"]
