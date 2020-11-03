from datetime import datetime

log_name = "log_name"

def echo_to_log(message: str):
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    with open(log_name, "a") as log_file:
        log_file.write(dt_string + " " + message + "\n")