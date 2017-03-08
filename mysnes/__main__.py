"""
__main__ - Main application
"""

# Standard library imports
import sys

# Local imports
from .console import Console

# Logging setup
import logging
log = logging.getLogger("main") # pylint: disable=invalid-name

# Constants

# Functions

# Classes

# Main application
def main():
    """ Creates console and runs the event loop. """
    log_level = logging.DEBUG# if options.debug else logging.INFO
    log_formatter = logging.Formatter("%(asctime)s.%(msecs)03d %(name)s(%(levelname)s): %(message)s", "%m/%d %H:%M:%S")
    stderr_handler = logging.StreamHandler()
    stderr_handler.setFormatter(log_formatter)
    # if options.log_filter:
        # stderr_handler.addFilter(logging.Filter(options.log_filter))
    root_logger = logging.root
    root_logger.setLevel(log_level)
    root_logger.addHandler(stderr_handler)
    
    log.info("SEGA?")
    
    console = Console(sys.argv[1])
    console.run()
    
if __name__ == "__main__":
    main()
    