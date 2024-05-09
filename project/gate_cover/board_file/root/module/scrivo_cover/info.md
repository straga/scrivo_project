
'''
  - cover:
      name: "MQTT Cover"
      command_topic: "home-assistant/cover/set"                 -> cmd_t
      position_topic: "home-assistant/cover/position"           -> pos_t
      availability:                                             -> avty        
        - topic: "home-assistant/cover/availability"
      set_position_topic: "home-assistant/cover/set_position"   -> set_pos_t
      qos: 0
      retain: true
      payload_open: "OPEN"                                      -> pl_open
      payload_close: "CLOSE"                                    -> pl_cls
      payload_stop: "STOP"                                      -> pl_stop
      position_open: 100                                        -> pos_open
      position_closed: 0                                        -> pos_clsd    
      payload_available: "online"
      payload_not_available: "offline"
      optimistic: false
      value_template: "{{ value.x }}"
      
      {"name":"*Gordijnen",
"uniq_id":"test_cover1",
"dev_cla":"curtain",
"pos_t":"domus/test/uit/screen",
"cmd_t":"domus/test_in",
"pl_open":"O1",
"pl_cls":"C1",
"pl_stop":"S1",
"pos_open":100,
"pos_clsd":0,
"set_pos_t":"domus/test/in",
"set_pos_tpl":"{ \"POSITION1\": {{ position }} }",
"pos_tpl":"{{value_json.POSITION1}}",
'''
