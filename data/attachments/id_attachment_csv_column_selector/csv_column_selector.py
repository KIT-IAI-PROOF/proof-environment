from sys import exit
import asyncio
import traceback

from proofcore.base import cliargparser
from proofcore.base.basewrapper import BaseWrapper, main
from proofcore.models.BlockStatus import BlockStatus
from proofcore.models.SimulationPhase import SimulationPhase
from proofcore.util.proofLogging import Logger, HandlerType
from proofcore.util.StringHelper import StringHelper

options, arguments = cliargparser.parse_known_args()

__log_file_name = "proof_CSV_Column_Selector_" + options.local_block_id + ".log"
logger = Logger('CSV_Column_Selector', handlers = [HandlerType.FILE], logging_dir=options.loggingDir, log_file_name =
__log_file_name, log_level=options.logLevel).get_logger()

"""
Read one CSV line per execution step and output the value of one selected
column.

Supported input formats:
"column_name_1,column_name_2,column_name_3"
"value_1,value_2,value_3"
or
"column_name_1;column_name_2;column_name_3"
"value_1;value_2;value_3"

The first matching header line is stored internally.
"""
class CSV_Column_Selector(BaseWrapper):
    """
    PROOF wrapper that extracts the value of one configured CSV column.

    The wrapper receives:
    - `column_name` during INIT
    - `input_string` during EXECUTE

    Runtime behavior:
    - The first line that contains `column_name` is interpreted as the header.
    - Later lines are interpreted as data rows.
    - The extracted field is written to `column_value`.
    - Because this template is configured to not wait for sync, each incoming EXECUTE value is processed immediately.
    """
    def __init__(self, opt=options) -> None:
        self.input_string = ""
        self.column_name = ""
        self.column_value = ""
        self.separator = ""
        self._string_helper = None
        logger.debug("__init__() -> initializing CSV_Column_Selector")
        # call the super class constructor to initialize the BaseWrapper with the options
        super(CSV_Column_Selector, self).__init__(bwoptions=opt)

    async def init(self, status=None, error_text="") -> None:
        logger.debug("init() -> initializing CSV_Column_Selector")
        try:
            # separator/column_name (INIT inputs) are already set by now, so seed the helper here.
            self._string_helper = StringHelper(separator=self.separator, logger=logger)
            await super(CSV_Column_Selector, self).init()

        except Exception as e:
            err_txt = "An error occurred when initializing the StringHelper: " + str(e) + "\n" + str(traceback.format_exc())
            logger.error(err_txt)
            await self.send_notify(SimulationPhase.INIT, BlockStatus.ERROR_INIT, str(e))

    async def step(self, status=None, error_text="") -> None:
        logger.debug(f"step() -> processing single CSV line for column_name={self.column_name}: {self.input_string}")
        try:
            # Extract the requested value from the current line using the stored header information.
            self.column_value = self._string_helper.extract_value_from_line(
                self.input_string,
                self.column_name,
            )

            logger.debug("Extracted column_value='%s'", self.column_value)

            # Reset the current input line
            self.input_string = ""
            await super(CSV_Column_Selector, self).step(BlockStatus.EXECUTION_STEP_FINISHED)

        except Exception as e:
            err_txt = "An error occurred when extracting values from line '" + self.input_string + "': " + str(e) + "\n" + str(traceback.format_exc())
            logger.error(err_txt)
            await self.send_notify(SimulationPhase.EXECUTE, BlockStatus.ERROR_STEP, str(e))


if __name__ == '__main__':
    try:
        logger.debug("The main method of csv_column_selector.py gets executed!")
        asyncio.run(main(wrapper=CSV_Column_Selector()))
    except KeyboardInterrupt:
        exit(0)
