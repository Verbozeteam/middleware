# middleware
Middleware between the Arduino and the control systems.

# Installation
- Create a virtual environment and make sure you use python 3.5+
    `virtualenv -p python3.5 .env`
- Install the requirements
    `pip install -r requirements.txt`

# Running tests
Make sure you are in the right virtual environment.

## Clone the arduino repository
Clone the [arduino](https://github.com/Verbozeteam/arduino) repository (in another folder, don't put it in this repo!). Make sure you properly set it up and install [shammam](https://github.com/Verbozeteam/shammam).

## Launch the Arduino emulator
`cd testing_utils`
`./initialize_arduino_emulator.py -e <path_to_arduino_repo>/emulation`

## Run the tests
From the root directory: `pytest`

