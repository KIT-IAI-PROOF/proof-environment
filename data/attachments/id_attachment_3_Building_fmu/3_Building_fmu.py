""" Version: 2026-10-05 """
from sys import exit
import asyncio

from proofcore.base import cliargparser
from proofcore.base.basewrapper import main
from proofcore.util.proofLogging import Logger, HandlerType
from proofcore.base.base_fmu_runner import BaseFmuRunner

options, arguments = cliargparser.parse_known_args()

# Local use of the custom PROOF logger. Each file can have its own logger.
__log_file_name = "proof_BuildingFmu_" + options.local_block_id + ".log"
logger = Logger('BuildingFmu', handlers = [HandlerType.FILE], logging_dir=options.loggingDir, log_file_name = __log_file_name, log_level=options.logLevel).get_logger()

class BuildingFmu(BaseFmuRunner):
    """
    RC thermal model of a building, executed as FMU.
    One FMU step (5 min) is performed per PROOF step.
    """
    def __init__(self, opt=options) -> None:
        # In- and outputs
        self.indoor_temp_init = None  # static input, set at INIT
        self.outdoor_temp = None
        self.p_hvac = None
        self.indoor_temp = None
        logger.debug("__init__() -> initializing BuildingFmu")
        super(BuildingFmu, self).__init__(options=opt)
        ## Overwrite FMU configuration
        self.fmu_name = "Building"
        # FMU time unit is hours (dt = 5/60 h in Building.mo)
        self.fmu_step_size = 5.0 / 60.0
        # FMU in-/output configuration
        # for start values
        self.input_dict = {"outdoor_temp": self.outdoor_temp, "p_hvac": self.p_hvac}
        self.output_list = ["indoor_temp"]

    async def init(self, **kwargs) -> None:
        # Static input is only available now, so the FMU parameter is set here
        if self.indoor_temp_init is not None:
            self.parameter_dict = {"indoor_temp_init": float(self.indoor_temp_init)}
        logger.debug(f"init() -> parameter_dict: {self.parameter_dict}")
        await super(BuildingFmu, self).init(**kwargs)

    async def step(self, **kwargs) -> None:
        logger.debug(f"step() -> inputs: {self.outdoor_temp}, {self.p_hvac}")
        # Assign values directly to respective inputs
        self.fmu_input_values = str([{"outdoor_temp": self.outdoor_temp, "p_hvac": self.p_hvac}])
        # This also updates self.<name> for all keys in self.output_list
        await super(BuildingFmu, self).step()
        logger.debug(f"step() -> resulting in {self.indoor_temp}")

if __name__ == '__main__':
    try:
        logger.debug("The main method of BuildingFmu.py gets executed!")
        asyncio.run(main(wrapper=BuildingFmu()))
    except KeyboardInterrupt:
        exit(0)
