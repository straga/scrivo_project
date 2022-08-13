
schema = '''
        {
          "_sch_0": {
            "_schema" : "_schema",
            "name": "switch_cfg",
            "sch": [
                      ["name", ["str",""] ],
                      ["pin", ["str", ""]],
                      ["state", ["int", null]],
                      ["restore", ["str", null]],
                      ["type", ["str", null]]
            ]
          }
        
        }
    '''

data = None
depend = ["pin"]


