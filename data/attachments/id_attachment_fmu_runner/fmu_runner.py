from sys import exit
import asyncio

from proofcore.base import cliargparser
from proofcore.base.basewrapper import main
from proofcore.util.proofLogging import Logger, HandlerType
from proofcore.base.base_fmu_runner import BaseFmuRunner

options, arguments = cliargparser.parse_known_args()

# Local use of the custom PROOF logger. Each file can have its own logger.
__log_file_name = "proof_FmuRunner_" + options.local_block_id + ".log"
logger = Logger('FmuRunner', handlers = [HandlerType.FILE], logging_dir=options.loggingDir, log_file_name = __log_file_name, log_level=options.logLevel).get_logger()

class FmuRunner(BaseFmuRunner):
    """
    A wrapper for the BaseFmuRunner
    """

if __name__ == '__main__':
    try:
        logger.debug("The main method of FmuRunner.py gets executed!")
        asyncio.run(main(wrapper=FmuRunner()))
    except KeyboardInterrupt:
        exit(0)
