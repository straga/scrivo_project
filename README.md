# scrivo
Scrivo - Helper for development for - Micropython/Python.



- #### \firmware

  - > Flash board:
  >
    > python -m esptool -p COM18 -b 460800 --before default_reset --after hard_reset --chip esp32  write_flash --flash_mode dio --flash_size detect --flash_freq 40m 0x1000 bootloader.bin 0x10000 partition-table.bin 0x15000 ota_data_initial.bin 0x20000 micropython.bin

    
  
  - #### **core**_flash4mb_espnow:  micropython +

    - scrivo: \src\scrivo, \src\scrivo_lib - lib for the modules and run in the thread.
    - espnow: https://github.com/glenn20/micropython/tree/espnow-g20
    - safe_lib: ftp, webrepl
    - uasyncio: add method for read UART - \src\u_lib\uasyncio -https://github.com/micropython/micropython/issues/8867

    

  - #### **psram**_flash4mb_espnow, psram_flash8mb_espnow:

     - scrivo: add to flash over FTP or UART
     -  espnow: https://github.com/glenn20/micropython/tree/espnow-g20
     -  safe_lib: ftp, webrepluasyncio: add method for read UART - \src\u_lib\uasyncio - https://github.com/micropython/micropython/issues/8867

    

- #### **\project**

- config for board: root\ \_conf\\ *.json - configure that. 

- root\ \_conf\\ data_net.json and root\ scret - configure Wifi

- root\ \_conf\\ data_board.json - board name, mqtt dev topic, hostname

- root\ \_conf\\ data_mqtt.json - configure mqtt

  

- #### XM AC Hisesne Control:

  - https://github.com/bannhead/pyaehw4a1/issues/1
	- https://github.com/htqwe22/device/blob/dev/src/protocol/protocol.c
  - **PSRAM** board:
     - vfs: project\ac_xm_hisense_control\board_psram
  - **Core** board:
     - vfs: project\ac_xm_hisense_control\board_core
  - Home Assistant Mqtt:
     - <img src="C:\Users\straga\AppData\Roaming\Typora\typora-user-images\image-20220813121245056.png" alt="image-20220813121245056" style="zoom:50%;" />