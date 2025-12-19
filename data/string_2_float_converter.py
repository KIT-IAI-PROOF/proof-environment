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

__log_file_name = "proof_String2FloatConverter_" + options.local_block_id + ".log"
# Local use of the custom PROOF logger. Each file can have its own logger.
logger = Logger('Float2String', handlers = [HandlerType.FILE], logging_dir=options.loggingDir, log_file_name = __log_file_name, log_level=options.logLevel).get_logger()

class String2FloatConverter(BaseWrapper):
    """
    A simple block that converts a float input to a string output.
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

    async def init(self) -> None:
        # Model logic
        logger.debug("processing init()")
        try:
            logger.debug("starting an init process")
            # Here you can initialize your model, e.g. read files, set up connections, etc.
        except Exception as e:
            logger.debug("handling an exception")
            await super(String2FloatConverter, self).init(BlockStatus.ERROR_INIT, str(e))
        else:
            logger.debug("executing super().init()")
            await super(String2FloatConverter, self).init(BlockStatus.INITIALIZED)

    async def step(self) -> None:
        # do nothing because all work is already done in the set_variables() method
        # also do not call the super().step() method
        pass


    async def finalize(self) -> None:
        # Model logic
        logger.debug("processing finalize()")
        try:
            logger.debug("starting a finalize process")
        except Exception as e:
            logger.debug("handling an exception")
            await super(String2FloatConverter, self).finalize(BlockStatus.ERROR_FINALIZE, str(e))
        else:
            logger.debug("executing super().finalize()")
            await super(String2FloatConverter, self).finalize(BlockStatus.FINALIZED)

    async def set_variables(self, variables: Dict, phase: SimulationPhase) -> None:
        for key, value in variables.items():
            setattr(self, key, value)

        logger.debug("processing set_variables(), variables: " + str(variables))

        try:
            if phase != SimulationPhase.INIT:
                self.float_output = float(self.string_input) if self.string_input is not None and self.string_input else 0.0
                await super(String2FloatConverter, self).step(BlockStatus.EXECUTION_STEP_FINISHED)
        except (ValueError, TypeError) as e:
            await self.send_notify(SimulationPhase.EXECUTE, BlockStatus.ERROR_STEP, str(e))



if __name__ == '__main__':
    try:
        logger.debug("The main method of String2FloatConverter.py gets executed!")
        asyncio.run(main(wrapper=String2FloatConverter()))
    except KeyboardInterrupt:
        exit(0)
