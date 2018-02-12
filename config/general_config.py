
class GENERAL_CONFIG:
    SIMULATE_ARDUINO = True
    SIMULATED_BOARD_NAME = "FT231X USB UART" #"arduino"
    BLUEPRINT_FILENAME = "blueprint.json"
    LOG_VERBOZITY = 3
    LOG_REGEX = None
    LOG_NUM_RUNS = 5 # will store logs for the last LOG_NUM_RUNS runs
    LOG_NUM_FILES = 5
    LOG_MAX_FILESIZE = 1024*1024

    SELECT_TIMEOUT = 1 # 1 second

