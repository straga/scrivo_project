
schema = '''
{
    "_sch_0": {
    "_schema" : "_schema",
    "name": "binary_sensor_cfg",
    "sch": [
              ["name", ["str",""] ],
              ["pin", ["str", ""]],
              ["trigger", ["list", ["IRQ_FALLING","IRQ_RISING"] ]],
              ["priority", ["int", null]],
              ["wake", ["str", null]],
              ["hard", ["bool", null]],
              ["on", ["int", 1]],
              ["on_data", ["list", null]]
    ]
  }
}
'''

depend = ["pin"]
data = None





