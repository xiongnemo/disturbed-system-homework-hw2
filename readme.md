# Disturbed System Homework 2

hardcoded server_size == 3

## Packet Header

`0x01`: set working mode

* 0x10: write mode(not used)
* 0x11: query mode
* 0x12: file transfer(client will use a new socket)

`0x02`: get server status

`0x03`: query

* following 1 byte for data id

`0x04`: set base file name

`0xFF`: bye

## Listening port

`server_port.py`

be sure that this port and the one above it is free to use.

## Logging

No. That logging is just for homework purpose.

Refer to `prgm_output/` for real prgm output.

## Server config

change it in `server_config.py`