# middleware
Middleware between the Arduino and the control systems.

# Installation
- Create a virtual environment and make sure you use python 3.5+
    `virtualenv -p python3.5 .env`
- Install the requirements
    `pip install -r requirements.txt`

# Running tests
- Make sure you are in the right virtual environment.
- Clone the [arduino](https://github.com/Verbozeteam/arduino) repository (in another folder, don't put it in this repo!). Make sure you properly set it up and install [shammam](https://github.com/Verbozeteam/shammam).
- Launch the Arduino emulator
`cd testing_utils`
`./initialize_arduino_emulator.py -e <path_to_arduino_repo>/emulation`
- Run the tests from the root directory: `pytest`

# Communicating with the middleware
Clients connected to the middleware can communicate with the middleware by sending a JSON object, which can be one of two types:
### State update
The client may send the middleware a "state update" to instruct it to change the state of a Thing. A state update object must have a field "thing" which contains the name of the Thing it wishes to send the update to. The rest of the message keys are the state update, and are Thing-dependent. e.g. The state update to switch on a light switch is
```
{
    "thing": "<ID of the thing>",
    "intensity": 1
}
```

### Control message
The client may send the middleware a control message to get/set connection metadata. A control message must NOT have a field "thing" in it, and must have a field "code" (integer) which contains the control code requested. The available control codes are:
- Code 0: Requests the middleware to send the blueprint to the client. The blueprint sent by the middleware looks like this:
```
{
    "config": {
        "rooms": [{
            <room configuration>
        }]
    },
    "<thing-id>": <thing state>,
    "<thing-id>": <thing state>,
    ...
}
```
- Code 1: Requests the middleware to send the state of a single Thing. The message should also contain a field "thing-id" which is the ID of the Thing that the client wishes to get its state.
- Code 2: Tells the middleware that the client is only interested in listening to future updates of a certain set of Things. The message should contain a field "things" which is a list of Thing IDs that the client wants to receive updates from. If no "things" field is given, then all updates are sent to the client.
