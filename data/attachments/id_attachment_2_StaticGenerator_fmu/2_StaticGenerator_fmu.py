""" Version: 2026-10-05 """
import argparse
import json
from sys import exit
from typing import Tuple, Dict, Any
import asyncio

from proofcore.base import cliargparser
from proofcore.base.basewrapper import main
from proofcore.models.BlockStatus import BlockStatus
from proofcore.models.NotifyMessage import NotifyMessage
from proofcore.models.ValueMessage import ValueMessage
from proofcore.models.SimulationPhase import SimulationPhase
from proofcore.util.proofLogging import Logger, HandlerType
from proofcore.base.base_fmu_runner import BaseFmuRunner

options, arguments = cliargparser.parse_known_args()

# Local use of the custom PROOF logger. Each file can have its own logger.
__log_file_name = "proof_StaticGeneratorFmu_" + options.local_block_id + ".log"
logger = Logger('StaticGeneratorFmu', handlers = [HandlerType.FILE], logging_dir=options.loggingDir, log_file_name = __log_file_name, log_level=options.logLevel).get_logger()

class StaticGeneratorFmu(BaseFmuRunner):
    """
    A simple block that converts a float input to a string output.
    It does not wait for a SYNC, but processes the input immediately.
    """
    def __init__(self, opt=options) -> None:
        # In- and outputs
        self.irradiance = None
        self.outdoor_temp = None
        self.pv_power = None
        logger.debug("__init__() -> initializing StaticGeneratorFmu")
        super(StaticGeneratorFmu, self).__init__(options=opt)
        ## Overwrite FMU configuration
        self.fmu_name = "PVCalculator"
        # FMU time unit is hours (5 min step, as in the other FMU blocks)
        self.fmu_step_size = 5.0 / 60.0
        # FMU in-/output configuration
        # for start values
        self.input_dict = {"irradiance": self.irradiance, "outdoor_temp": self.outdoor_temp}
        self.output_list = ["pv_power"]

    async def step(self, **kwargs) -> None:
        logger.debug(f"step() -> inputs: {self.irradiance}, {self.outdoor_temp}")
        # Assign values directly to respective inputs
        self.fmu_input_values = str([{"irradiance": self.irradiance, "outdoor_temp": self.outdoor_temp}])
        # This also updates self.<name> for all keys in self.output_list
        await super(StaticGeneratorFmu, self).step()
        logger.debug(f"step() -> resulting in {self.pv_power}")

if __name__ == '__main__':
    try:
        logger.debug("The main method of StaticGeneratorFmu.py gets executed!")
        asyncio.run(main(wrapper=StaticGeneratorFmu()))
    except KeyboardInterrupt:
        exit(0)
