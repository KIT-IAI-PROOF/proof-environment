""" Version: 2025-07-25 """
import argparse
import json
from sys import exit
from typing import Tuple, Dict, Any
import asyncio

from proofcore.base import cliargparser
from proofcore.base.basewrapper import BaseWrapper, main
from proofcore.models.SimulationPhase import SimulationPhase
from proofcore.models.BlockStatus import BlockStatus
from proofcore.models.NotifyMessage import NotifyMessage
from proofcore.models.ValueMessage import ValueMessage
from proofcore.util.proofLogging import Logger, HandlerType

options, arguments = cliargparser.parse_known_args()

# Local use of the custom PROOF logger. Each file can have its own logger.
__log_file_name = "proof_String2FloatConverter_" + options.local_block_id + ".log"
logger = Logger('String2Float', handlers = [HandlerType.FILE], logging_dir=options.loggingDir, log_file_name = __log_file_name, log_level=options.logLevel).get_logger()

class String2FloatConverter(BaseWrapper):
    """
    A simple block that converts a string input to a float output.
    It does not wait for a SYNC, but processes the input immediately.
    """
    def __init__(self, opt=options) -> None:
        # define and initialize the static inputs and attributes of the model
        # The input and output names are defined in the CLI arguments.
        # Default values must be set here, because attribute values may not be required for the model (this is defined in the PROOF Block/Template)
        # examples:
        #   self.A = 0.0  # -> defined as STEPBASED_STATIC in the PROOF Block/Template and will be set in init()
        #   self.B = 0.0  # -> defined as STEPBASED in the PROOF Block/Template and will be set in step()
        #   self.myValue = 0.0  # my own value -> Output, also defined in the PROOF Block/Template, can be set anywhere

        # call the super class constructor to initialize the BaseWrapper with the options
        self.string_input = None
        self.float_output = None
        logger.debug("__init__() -> initializing String2FloatConverter")
        super(String2FloatConverter, self).__init__(bwoptions=opt)

    async def step(self) -> None:

        logger.debug(f"transforming string '{self.string_input}' to float...")

        try:
            self.float_output = float(self.string_input) if self.string_input is not None and self.string_input else 0.0
            logger.debug(f"Resulting float is {self.float_output}.")
            await super(String2FloatConverter, self).step(BlockStatus.EXECUTION_STEP_FINISHED)
        except (ValueError, TypeError) as e:
            await self.send_notify(SimulationPhase.EXECUTE, BlockStatus.ERROR_STEP, str(e))


if __name__ == '__main__':
    try:
        logger.debug("The main method of String2FloatConverter.py gets executed!")
        asyncio.run(main(wrapper=String2FloatConverter()))
    except KeyboardInterrupt:
        exit(0)
