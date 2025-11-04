""" Version: 23.07.2025
The FileWriter module is a Python Wrapper for PROOF that allows users to write data to a file.
It gets initialized with a file name and path, and can write data to the file in either write or append mode.
The data to be written is set in the `step()` method, and the file is closed in the `finalize()` method.
"""
import argparse
import traceback
import asyncio

from proofcore.base import cliargparser
from proofcore.models.SimulationPhase import SimulationPhase
from proofcore.base.basewrapper import BaseWrapper, main
from proofcore.models.BlockStatus import BlockStatus
from proofcore.models.SimulationPhase import SimulationPhase
from proofcore.util.proofLogging import Logger, HandlerType
from sys import exit
from typing import Dict

options, arguments = cliargparser.parse_known_args()


# Use of the custom PROOF logger. Each file has its own logger.
log_file_name = "proof_FileWriterLogger_" + str(options.local_block_id) + ".log"
logger = Logger('FileWriterLogger', handlers = [HandlerType.FILE], logging_dir=options.loggingDir, log_file_name = log_file_name, log_level=options.logLevel).get_logger()

class FileWriter(BaseWrapper):
    def __init__(self, opt=options) -> None:
        logger.debug("options: " + str(opt) + "\n===============================================")
        # output values
        self.communication_point=-1
        self.currentStep = 1
        self.file_name = None      # STEPBASED_STATIC, required input, set in init()
        self.file_path = None      # local path to the file to be written to, set in init()
        self.file = None           # file object, opened in init()
        self.mode = 'w'            # write mode, can be 'w' for write or 'a' for append, set in init()
        self.waitForSync = None    # wait for a SYNC before writing the data, can be set in the PROOF Block/Template
        self._wait_for_sync = True # internal flag to wait for a SYNC, default is True
        self.additionalCRLF = None # if True, an additional Carrage Return and Line Feed will be printed. This can be important when values without CRLF should be written
        self._additional_clrf = False # internal flag for given worker value
        self.data = ""             # data to be written to the file, set in step()
        #logger.debug("__init__() -> FileWriter initialized \n")

        super(FileWriter, self).__init__(bwoptions=opt)

    async def init(self) -> None:
        logger.debug("initializing FileWriter, Values given:")
        self.file_path = self.file_name
        logger.debug("filename: " + str(self.file_path))
        logger.debug("inputs: " + str(self.inputs))
        logger.debug("outputs: " + str(self.outputs))

        self._wait_for_sync = self.waitForSync.lower() == "true" if self.waitForSync is not None else False
        self._additional_clrf = self.additionalCRLF.lower() == "true" if self.additionalCRLF is not None else False
        logger.debug("waitForSync: " + str(self._wait_for_sync) + ",  additionalCRLF: " + str(self._additional_clrf) )

        try:
            self.file = open(self.file_path, self.mode)
            await super(FileWriter, self).init()
        except Exception as e:
            error_txt = "Error opening file '" + self.file_path + "' -> " + str(e) + "\n" + str(traceback.format_exc())
            logger.error(error_txt)
            await self.send_notify(SimulationPhase.INIT, BlockStatus.ERROR_INIT, error_txt)


    async def step(self) -> None:
        self.currentStep += 1
        logger.debug(f"processing STEP(CS: {self.currentStep})")
        try:
            if self.data is not None:
                self.file.write(self.data)
                if self._additional_clrf:
                    self.file.write("\n")
                if self.mode == 'a':
                    logger.debug(f"processing STEP; data appended to file '{self.data}'")
                else:
                    logger.debug(f"processing STEP; data written to file '{self.data}'")
                await super(FileWriter, self).send_notify(SimulationPhase.EXECUTE, BlockStatus.EXECUTION_STEP_FINISHED, error_text="")
        except Exception as e:
            error_txt = "Error writing to file '" + self.file_path + "' -> " + str(e) + "\n" + str(traceback.format_exc())
            logger.error(error_txt)
            await self.send_notify(SimulationPhase.EXECUTE, BlockStatus.ERROR_INIT, error_txt)

    async def finalize(self) -> None:
        logger.debug("executing the finalize method")
        if self.file is not None:
            self.file.close()
            self.file = None
        else:
            raise ValueError("ERROR closing file '" + self.file_path + "':  File is not opened yet")
        await super(FileWriter, self).finalize()

    # overwriting the following BaseWrapper function to process wait_for_sync and
    # send the data immediately if not waiting for a SYNC
    async def set_variables(self, variables: Dict, phase: SimulationPhase) -> None:
        for key, value in variables.items():
            setattr(self, key, value)

        if self._wait_for_sync:
            logger.debug( "waiting for SYNC, then sending value, CP: "  + str(self.communication_point))
        else:
            logger.debug( "Do not wait for a SYNC, sending value and notify at once ..." )
            await self.step()


if __name__ == '__main__':
    try:
        asyncio.run(main(wrapper=FileWriter()))
        logger.debug("The main method of the file_line_provider.py gets executed!")
    except KeyboardInterrupt:
        exit(0)


