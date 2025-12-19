""" Version: 2025-07-25 """
import argparse
import json
from sys import exit
from typing import Tuple, Dict, Any
import asyncio
import time
import traceback

from proofcore.base import cliargparser
from proofcore.base.basewrapper import BaseWrapper, main
from proofcore.models.SimulationPhase import SimulationPhase
from proofcore.models.BlockStatus import BlockStatus
from proofcore.models.NotifyMessage import NotifyMessage
from proofcore.models.ValueMessage import ValueMessage
from proofcore.util.proofLogging import Logger, HandlerType

options, arguments = cliargparser.parse_known_args()

__log_file_name = "proof_ProcTimeSim_" + options.local_block_id + ".log"
# Local use of the custom PROOF logger. Each file can have its own logger.
logger = Logger('ProcTimeSim', handlers = [HandlerType.FILE], logging_dir=options.loggingDir, log_file_name = __log_file_name, log_level=options.logLevel).get_logger()

class ProcTimeSimulator(BaseWrapper):
    """
    A simple block that simulates a long-lasting process.
    It does not wait for a SYNC, but processes the input immediately.
    """
    def __init__(self, opt=options) -> None:
        self.opt_input = None
        self.opt_output = None
        self.proc_time = 1.0
        logger.debug("__init__() -> initializing ProcTimeSimulator")
        super(ProcTimeSimulator, self).__init__(bwoptions=opt)

    async def init(self) -> None:
        # Model logic
        logger.debug("processing init()")
        try:
            self.proc_time = self.proc_time if self.proc_time is not None and self.proc_time else 1.0
        except Exception as e:
            logger.debug("handling an exception")
            await super(ProcTimeSimulator, self).init(BlockStatus.ERROR_INIT, str(e))
        else:
            logger.debug("executing super().init()")
            await super(ProcTimeSimulator, self).init(BlockStatus.INITIALIZED)

    async def step(self) -> None:
        logger.debug(f"processing STEP(CP: {self.communication_point};  proc_time: {self.proc_time}")
        try:
            logger.debug(f"process sleeping for {self.proc_time} seconds) to simulate processing time")
            time.sleep(self.proc_time)
            logger.debug(f"process continued after {self.proc_time} seconds")
        except Exception as e:
            logger.error("handling an exception in STEP")
            error_txt = "Error in step() " + str(traceback.format_exc())
            logger.error(error_txt)
            await self.send_notify(SimulationPhase.STEP, BlockStatus.ERROR_STEP, error_txt)


    # async def finalize(self) -> None:
    #     # Model logic
    #     logger.debug("processing finalize()")
    #     try:
    #         logger.debug("starting a finalize process")
    #     except Exception as e:
    #         logger.debug("handling an exception")
    #         await super(ProcTimeSimulator, self).finalize(BlockStatus.ERROR_FINALIZE, str(e))
    #     else:
    #         logger.debug("executing super().finalize()")
    #         await super(ProcTimeSimulator, self).finalize(BlockStatus.FINALIZED)


if __name__ == '__main__':
    try:
        logger.debug("The main method of ProcTimeSimulator.py gets executed!")
        asyncio.run(main(wrapper=ProcTimeSimulator()))
    except KeyboardInterrupt:
        exit(0)
