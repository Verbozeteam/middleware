# middleware
Middleware between the Arduino and the control systems.

# Running tests
Make sure you are in the right virtual environment.

## Clone the arduino repository
Clone the [arduino](https://github.com/Verbozeteam/arduino) repository. Make sure you properly set it up and install [shammam](https://github.com/Verbozeteam/shammam).

## Launch the Arduino emulator
`cd testing_utils`
`./initialize_arduino_emulator.py -e <path_to_arduino_repo>/emulation`

## Run the tests
From the root directory: `python -m pytest`

