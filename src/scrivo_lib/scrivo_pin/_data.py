
schema = '''
    {
      "_sch_0": {
        "_schema" : "_schema",
        "name": "pin_cfg",
        "sch": [
                  ["name", ["str",""] ],
                  ["number", ["int", 0] ],
                  ["inverted", ["bool", null]],
                  ["mode", ["str", null]],
                  ["pull", ["str", null]],
                  ["value", ["int", null]],
                  ["drive", ["str", null]],
                  ["alt", ["str", null]],
                  ["pref", ["str", null]],
                  ["pcb_name", ["str", ""]]
        ]
      }
    }
    '''

data = None
depend = ["board"]


