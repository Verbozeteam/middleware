
class Core(object):
    cmd_args = None
    blueprint = None
    hw_manager = None

    @staticmethod
    def initialize():
        # Parse command line arguments
        parser = argparse.ArgumentParser(description='Middleware core')
        parser.add_argument("-b", "--blueprint", required=False, type=str, help="Building configuration file", default="blueprint.json")
        Core.cmd_args = parser.parse_args()

        Log.info("Initializing the core...")

        # Load blueprint of the building
        Core.blueprint = Blueprint(Core.cmd_args.blueprint)

        # Initialize hardware manager (Arduino's and such...)
        Core.hw_manager = HardwareManager()

    @staticmethod
    def run():
        Log.info("Running the core...")
        while True:
            cur_time_s = time.time()
            Core.hw_manager.update(cur_time_s)

if __name__ == '__main__':
    from hardware import HardwareManager
    from things import Blueprint
    from logs import Log
    import time
    import argparse

    # Initialize logging
    Log.initialize()

    # Initialize and run the core
    Core.initialize()
    Core.run()
