""" Version: 23.07.2025 """
import traceback
import asyncio

from proofcore.base import cliargparser
from proofcore.models.SimulationPhase import SimulationPhase
from proofcore.base.basewrapper import BaseWrapper, main
from proofcore.models.BlockStatus import BlockStatus
from proofcore.util.proofLogging import Logger, HandlerType
from sys import exit

options, arguments = cliargparser.parse_known_args()

# Use of the custom PROOF logger. Each file has its own logger.
log_file_name = "proof_FileLineProviderLogger_" + str(options.local_block_id) + ".log"
logger = Logger('FileLineProviderLogger', handlers = [HandlerType.FILE], logging_dir=options.loggingDir, log_file_name = log_file_name, log_level=options.logLevel).get_logger()

class FileLineProvider(BaseWrapper):
    """
    The FileLineProvider module is a Python Wrapper for PROOF that allows users to read lines from a file and provide this line as output.
    The attribute `file_name` is set to the file path, and the file is opened in read mode.
    the attribute `ignore_first_line` can be set to True to skip the first line of the file. This is often useful for files with headers, e.g. CSV files.
    the attribute `num_steps` defines how many lines should be read from the file and provided. If the end of the file is reached before this number, the execution will finish.
    """
    def __init__(self, opt=options) -> None:
        logger.debug("options: " + str(opt) + "\n===============================================")

        self.communication_point=-1     # local communication point for debugging, set by a value message before step() by the Worker
        self.currentStep = 0            # local current step number
        self.currentRow = 0             # local current row number
        self.num_steps = 10             # number of lines to read from the file, can be set in the PROOF Block/Template
        self.line = None                # local variable to store the current line read from the file, set in step()
        self.file_name = None           # STEPBASED_STATIC, required input, set in init()
        self.file_path = None           # local path to the file to be read, set in init()
        self.file = None                # file object, opened in init()
        self.mode = 'r'                 # read mode of the file
        self.ignore_first_line = "false"# can be set to True to ignore the first line of the file, e.g. for CSV files with headers
        self._ignore_first_line = False # internal flag to ignore the first line, default is False

        super(FileLineProvider, self).__init__(bwoptions=opt)

    async def init(self) -> None:
        logger.debug("initializing FileLineProvider, Values given:")
        self.file_path = self.file_name
        logger.debug("file_name: " + str(self.file_path))
        logger.debug("inputs: " + str(self.inputs))
        logger.debug("outputs: " + str(self.outputs))
        logger.debug("ignore_first_line: " + str(self.ignore_first_line))

        self._ignore_first_line = self.ignore_first_line.lower() == "true" if self.ignore_first_line is not None else False
        logger.debug("ignore_first_line: " + str(self._ignore_first_line))

        try:
            self.file = open(self.file_path, self.mode)
            if self._ignore_first_line:
                self.file.readline()

            await super(FileLineProvider, self).init()

        except Exception as e:
            error_txt = "Error opening file '" + self.file_path + "' -> " + str(e) + "\n" + str(traceback.format_exc())
            logger.error(error_txt)
            await self.send_notify(SimulationPhase.INIT, BlockStatus.ERROR_INIT, error_txt)


    async def step(self) -> None:
        self.currentStep += 1
        logger.debug(f"processing STEP(CS: {self.currentStep};  num_steps: {self.num_steps})")
        try:
            if self.currentStep > self.num_steps:
                logger.debug(f"processing STEP; given number of steps reached ({self.num_steps}) -> EXECUTION FINISHED ")
                await super(FileLineProvider, self).step(BlockStatus.EXECUTION_FINISHED)
                return

            if self.file is not None:
                self.line = self.file.readline()
                self.currentRow += 1
            else:
                raise ValueError("Error reading file '" + self.file_path + "': file is not opened yet")

            logger.debug(f"LINE for CP {self.communication_point}: \n" + str(self.line))
            await super(FileLineProvider, self).step(BlockStatus.EXECUTION_STEP_FINISHED)

        except Exception as e:
            error_txt = "Error in step() reading file line of '" + self.file_path + "' -> " + str(e) + "\n" + str(traceback.format_exc())
            logger.error(error_txt)
            await self.send_notify(SimulationPhase.INIT, BlockStatus.ERROR_INIT, error_txt)

    async def finalize(self) -> None:
        logger.debug("finalize() -> FileLineProvider executed the finalize method")
        if self.file is not None:
            self.file.close()
            self.file = None
        else:
            raise ValueError("ERROR closing file '" + self.file_path + "':  File is not opened yet")
        await super(FileLineProvider, self).finalize()


if __name__ == '__main__':
    try:
        asyncio.run(main(wrapper=FileLineProvider()))
        logger.debug("The main method of the file_line_provider.py gets executed!")
    except KeyboardInterrupt:
        exit(0)


