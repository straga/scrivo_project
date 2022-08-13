
schema = '''
    {
      "_sch_0": {
        "_schema" : "_schema",
        "name": "i2c_cfg",
        "sch": [
                  ["name", ["str",""] ],
                  ["id", ["int", 0] ],
                  ["freq", ["int", 400000]],
                  ["scl", ["str", null]],
                  ["sda", ["str", null]]
        ]
      }
    }
    '''

data = None
depend = ["pin"]


