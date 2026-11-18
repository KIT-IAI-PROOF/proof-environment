""" Version: 2026-10-05 """
from sys import exit
import asyncio

from proofcore.base import cliargparser
from proofcore.base.basewrapper import main
from proofcore.util.proofLogging import Logger, HandlerType
from proofcore.base.base_fmu_runner import BaseFmuRunner

options, arguments = cliargparser.parse_known_args()

# Local use of the custom PROOF logger. Each file can have its own logger.
__log_file_name = "proof_ControllerFmu_" + options.local_block_id + ".log"
logger = Logger('ControllerFmu', handlers = [HandlerType.FILE], logging_dir=options.loggingDir, log_file_name = __log_file_name, log_level=options.logLevel).get_logger()

class ControllerFmu(BaseFmuRunner):
    """
    Discrete PID controller (PIDControllerStateful FMU) computing the HVAC power.
    One FMU step (5 min) is performed per PROOF step.
    """
    def __init__(self, opt=options) -> None:
        # In- and outputs
        self.indoor_temp = None
        self.price = None
        self.pv_power = None
        self.p_hvac = None
        logger.debug("__init__() -> initializing ControllerFmu")
        super(ControllerFmu, self).__init__(options=opt)
        ## Overwrite FMU configuration
        self.fmu_name = "PIDControllerStateful"
        # FMU time unit is hours (dt = 5/60 h in PIDControllerStateful.mo)
        self.fmu_step_size = 5.0 / 60.0
        # FMU in-/output configuration
        # for start values
        self.input_dict = {"indoor_temp": self.indoor_temp, "price": self.price, "pv_power": self.pv_power}
        self.output_list = ["p_hvac"]

    async def step(self, **kwargs) -> None:
        logger.debug(f"step() -> inputs: {self.indoor_temp}, {self.price}, {self.pv_power}")
        # Assign values directly to respective inputs
        self.fmu_input_values = str([{"indoor_temp": self.indoor_temp, "price": self.price, "pv_power": self.pv_power}])
        # This also updates self.<name> for all keys in self.output_list
        await super(ControllerFmu, self).step()
        logger.debug(f"step() -> resulting in {self.p_hvac}")

if __name__ == '__main__':
    try:
        logger.debug("The main method of ControllerFmu.py gets executed!")
        asyncio.run(main(wrapper=ControllerFmu()))
    except KeyboardInterrupt:
        exit(0)
