""" Version: 2026-10-05 """
from sys import exit
import asyncio

from proofcore.base import cliargparser
from proofcore.base.basewrapper import main
from proofcore.util.proofLogging import Logger, HandlerType
from proofcore.base.base_fmu_runner import BaseFmuRunner

options, arguments = cliargparser.parse_known_args()

# Local use of the custom PROOF logger. Each file can have its own logger.
__log_file_name = "proof_DataFeederFmu_" + options.local_block_id + ".log"
logger = Logger('DataFeederFmu', handlers = [HandlerType.FILE], logging_dir=options.loggingDir, log_file_name = __log_file_name, log_level=options.logLevel).get_logger()

class DataFeederFmu(BaseFmuRunner):
    """
    Provides irradiance, outdoor temperature and price time series from the DataFeeder FMU.
    It has no inputs and does one FMU step (5 min) per PROOF step.
    """
    def __init__(self, opt=options) -> None:
        # Outputs
        self.irradiance = None
        self.outdoor_temp = None
        self.price = None
        logger.debug("__init__() -> initializing DataFeederFmu")
        super(DataFeederFmu, self).__init__(options=opt)
        ## Overwrite FMU configuration
        self.fmu_name = "DataFeeder"
        # FMU time unit is hours (dt = 5/60 h in DataFeeder.mo)
        self.fmu_step_size = 5.0 / 60.0
        # FMU in-/output configuration
        self.input_dict = {}
        self.output_list = ["irradiance", "outdoor_temp", "price"]

    async def step(self, **kwargs) -> None:
        # This also updates self.<name> for all keys in self.output_list
        await super(DataFeederFmu, self).step()
        logger.debug(f"step() -> resulting in irradiance={self.irradiance}, outdoor_temp={self.outdoor_temp}, price={self.price}")

if __name__ == '__main__':
    try:
        logger.debug("The main method of DataFeederFmu.py gets executed!")
        asyncio.run(main(wrapper=DataFeederFmu()))
    except KeyboardInterrupt:
        exit(0)
