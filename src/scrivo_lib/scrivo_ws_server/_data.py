
schema = '''
{
    "ws_server_sch": {
        "_schema" : "_schema",
        "name": "ws_server",
        "sch": [
            ["name", ["str",""] ],
            ["addr", ["str", ""] ],
            ["port", ["int", 8083]]
        ]
    }
}
'''
data = None
depend = ["net"]


