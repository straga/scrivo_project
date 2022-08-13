
schema = '''{
      "_sch_0": {
        "_schema" : "_schema",
        "name": "board_cfg",
        "sch": [
                  ["name", ["str",""]],
                  ["board", ["str", ""]],
                  ["hostname", ["str", ""]],
                  ["uid", ["str", ""]],
                  ["topic", ["str", ""]]
        ]
      }
    }'''

depend = []

data = '''{
  "board": {
    "_schema" : "board_cfg",
    "name": "default",
    "board": "any",
    "hostname": "upy.local",
    "uid": "",
    "topic": "dev/any"
  }
}'''





