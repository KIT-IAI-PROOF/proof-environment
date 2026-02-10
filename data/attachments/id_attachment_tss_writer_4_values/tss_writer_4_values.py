""" Version: 23.07.2025
The TSSWriter4Values module is a Python Wrapper for PROOF that allows users to write up to four values to a TSS (Time Series Service)
It can either write the values immediately or wait for a SYNC before writing them.
After each step, the values are sent to the TSS, and the attributes are reset if configured (set in the PROOF Block/Template).
If configured, the data is sent to the TSS with a communication point, which can be used for the interpretation of the data in the TSS.
"""
import json
import argparse
import requests
import time
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
log_file_name = "proof_TSSWriter4Values_" + str(options.local_block_id) + ".log"
logger = Logger('TSSWriter4ValuesLogger', handlers = [HandlerType.FILE], logging_dir=options.loggingDir, log_file_name = log_file_name, log_level=options.logLevel).get_logger()

class TSSWriter4Values(BaseWrapper):
    """
    The TSSWriter4Values module is a Python Wrapper for PROOF that allows users to write up to four values to a TSS (Time Series Service)
    It can either write the values immediately or wait for a SYNC before writing them.
    After each step, the values are sent to the TSS, and the attributes are reset if configured (set in the PROOF Block/Template).
    If configured, the data is sent to the TSS with a communication point, which can be used for the interpretation of the data in the TSS.
    """

    def __init__(self, opt=options) -> None:
        # given by the Worker, set in the PROOF Block/Template:
        self.tss_writer_url = None  # URL of the TSS Writer
        self.tags=None              # tags for the TSS data
        self.resetInput = None      # whether to reset the input values after each step
        self._reset_input = True    # local variable, because self.resetInput is provided as a string
        self.writeCP = None         # whether to write the communication point to the TSS data
        self._write_cp = False      # local variable, because self.writeCP is provided as a string

        # local variables, used for tss data building and sending
        self.timeUnit="ms"
        self.headers = '{\"Content-Type\": \"application/json\"}'
        self.timeFactor = 1

        self.input=""
        self.value_1=None
        self.value_2=None
        self.value_3=None
        self.value_4=None
        self.valName_1="Value-1"
        self.valName_2="Value-2"
        self.valName_3="Value-3"
        self.valName_4="Value-4"
        self.communication_point=0
        self.resetInput = None
        self._reset_input = True
        self.communication_point=0
        logger.debug("__init__() -> initializing TSSWriter4Values")

        super(TSSWriter4Values, self).__init__(bwoptions=opt)

    async def init(self, status=None, error_text="") -> None:
        logger.debug("init() -> initializing TSSWriter4Values, URL received from worker for the tss-writer: " + self.tss_writer_url)

        try:
            self._reset_input = self.resetInput.lower() == "true" if self.resetInput is not None else False
            self._write_cp = self.writeCP.lower() == "true" if self.writeCP is not None else False

            if self.timeUnit is not None:
                await self.set_time_factor()

            if self.tss_writer_url is None:
                logger.debug("TSS URL (tss_writer_url) is not set!")
                await super(TSSWriter4Values, self).init(BlockStatus.ERROR_STEP, "Error initializing TSSWriter4Values, reason: tss_writer_url is not set!")

            logger.debug("(1) INIT() processed\n")

            await super(TSSWriter4Values, self).init()
        except Exception as e:
            err_txt = "An error occurred in init: " + str(e) + "\n" + str(traceback.format_exc())
            self.logger.debug(err_txt)
            await self.send_notify(SimulationPhase.INIT, BlockStatus.ERROR_STEP, error_text=err_txt)

    async def step(self, status=None, error_text="") -> None:
        logger.debug("processing STEP()\n")

        await self.push_value()
        # not necessary:   nothing happens there with respect to TSSWriter (no outputs)
        #await super(TSSWriter4Values, self).step()

    async def finalize(self, status=None, error_text="") -> None:
        logger.debug("finalize() -> TSSWriter4Values executed the finalize method")
        await super(TSSWriter4Values, self).finalize()

    async def reset_attributes(self):
        self.value_1=None
        self.value_2=None
        self.value_3=None
        self.value_4=None

    async def build_ts_data(self):
        #jsonStr = "{\"time\": " + str(round(time.time())) + ",\"fields\":"
        logger.debug("build_ts_data() entered")
        try:
            body = {'time': round(time.time()*self.timeFactor)}

            valdict = {}
            if getattr(self, 'value_1') is not None:
                valdict[ self.valName_1 ] = self.value_1
            if getattr(self, 'value_2') is not None:
                valdict[ self.valName_2 ] = self.value_2
            if getattr(self, 'value_3') is not None:
                valdict[ self.valName_3 ] = self.value_3
            if getattr(self, 'value_4') is not None:
                valdict[ self.valName_4 ] = self.value_4

            if self._write_cp:
                valdict['CP'] = self.communication_point

            # if no value is set:
            if len(valdict) == 0:
                logger.debug("No value is set during step!")
                return None

            body['fields'] = valdict

            if self.tags is not None:
                body['tags'] = json.loads(self.tags)

            #print("\n=> resulting TSS data: ", body)
            logger.debug("build_ts_data() exiting, body: " + str(body))
            return [body]
        except Exception as e:
            err_txt = "Error in build_ts_data() -> " + str(e) + "\n" + str(traceback.format_exc())
            self.logger.debug(err_txt)
            await self.send_notify(SimulationPhase.INIT, BlockStatus.ERROR_STEP, error_text=err_txt)
            return None

    async def push_value(self) -> None:
        logger.debug("push_value() -> sending the values to the TSS")

        try:
            payload = await self.build_ts_data()
            logger.debug("push_value() -> payload built: " + str(payload))
            if payload is None:
                logger.debug("no data given => no data written to TSS")
                await super(TSSWriter4Values, self).step()
                return

            load_headers = json.loads(self.headers)
            # if self.communication_point and self.communication_point > 6:
            #     logger.debug("push_value() -> loadHeader: " + str(load_headers))
            #     logger.debug("push_value() -> payload: " + str(payload))
            rc = requests.request("POST", self.tss_writer_url, json=payload, headers=load_headers)
            logger.debug("push_value() -> request finished, rc=" + str(rc))
            #rc = requests.request("POST", self.tss_writer_url, json=[json.loads(payload)], headers=load_headers)
            if not rc.ok:  # ok, when rc < 400
                logger.debug("Reason (reason): " + str(rc.reason))
                logger.debug("Reason (text)  : " + str(rc.text))
                return await self.send_notify(SimulationPhase.EXECUTE, BlockStatus.ERROR_STEP, "Error writing to TSS, RC=" + str(rc.status_code))
        except (Exception,BaseException)  as e:
            logger.debug("push_value() -> in except")
            logger.error("Error in push_value()/step() -> " + str(e) + "\n" + str(traceback.format_exc()))
            await self.send_notify(SimulationPhase.EXECUTE, BlockStatus.ERROR_STEP, str(e))
        else:  #executing the following code if no exception
            logger.debug("push_value() -> in else")
            if self._reset_input:
                await self.reset_attributes()

        logger.debug("push_value: value sent, now sending notify for CP: " + str(self.communication_point))
        await self.send_notify(SimulationPhase.EXECUTE, block_status=BlockStatus.EXECUTION_STEP_FINISHED, error_text="")
        logger.debug("push_value: NOTIFY Message sent ...")

    async def set_time_factor(self):
        match self.timeUnit:
            case "s":
                self.timeFactor = 1
            case "ms":
                self.timeFactor = 1000
            case "ns":
                self.timeFactor = 1000000
            case "m":
                self.timeFactor = 1/60

    # async def start(self, wrapper):
    #     self.wrapper = wrapper
    #     await wrapper.main()

# async def main():
#     try:
#         wrapper = TSSWriter4Values()
#         await wrapper.start(wrapper=wrapper)
#         logger.debug("The main method of the tss_writer_4_values.py gets executed!")
#     except KeyboardInterrupt:
#         exit(0)

if __name__ == '__main__':
    try:
        asyncio.run(main(wrapper=TSSWriter4Values()))
        logger.debug("The main method of TSSWriter4Values gets executed!")
    except KeyboardInterrupt:
        exit(0)
