import traceback
import asyncio
import math
import csv
from itertools import zip_longest

from proofcore.base import cliargparser
from proofcore.models.SimulationPhase import SimulationPhase
from proofcore.base.basewrapper import BaseWrapper, main
from proofcore.models.BlockStatus import BlockStatus
from proofcore.util.proofLogging import Logger, HandlerType
from sys import exit

options, arguments = cliargparser.parse_known_args()

# Logger
log_file_name = f"proof_DataFeeder_{options.local_block_id}.log"
logger = Logger('DataFeederLogger', handlers=[HandlerType.FILE], logging_dir=options.loggingDir,
                log_file_name=log_file_name, log_level=options.logLevel).get_logger()


class DataFeederWrapper(BaseWrapper):
    def __init__(self, opt=options) -> None:
        self.step_counter = 0
        self.df = None

        self.irradiance = None
        self.outdoor_temp = None
        self.price = None

        self.history = {
            'step': [],
            'irradiance': [],
            'outdoor_temp': [],
            'price': []
        }
        super(DataFeederWrapper, self).__init__(bwoptions=options)
        logger.info("DataFeeder initialized.")

    async def init(self, status=None, error_text="") -> None:
        try:
            irr_day = [int(1000 * math.sin(math.pi * i / 144)) for i in range(144)]
            irradiance_data = [0] * 72 + irr_day + [0] * 72
            temp_data = [round(30.0 - 5.0 * math.cos(2 * math.pi * (i - 36) / 288), 1) for i in range(288)]
            price_data = [0.5] * 84 + [1.2] * 36 + [0.8] * 84 + [1.5] * 48 + [0.5] * 36
            self.df = {
                'irradiance': irradiance_data,
                'outdoor_temp': temp_data,
                'price': price_data
            }
            logger.info(f"Data loaded successfully: df=\n{self.df}.")
        except Exception as e:
            error_txt = "Error in init() -> " + str(e)
            logger.error(error_txt)
            await self.send_notify(SimulationPhase.INIT, BlockStatus.ERROR_INIT, error_txt)

        await super(DataFeederWrapper, self).init()

    async def step(self, status=None, error_text="") -> None:
        try:
            idx = self.step_counter

            self.irradiance = float(self.df['irradiance'][idx])
            self.outdoor_temp = float(self.df['outdoor_temp'][idx])
            self.price = float(self.df['price'][idx])

            logger.debug(f"Step {self.step_counter}: Output 'irradiance': {self.irradiance}, 'outdoor_temp': {self.outdoor_temp}, 'price': {self.price}")

            self.history['step'].append(self.step_counter)
            self.history['irradiance'].append(self.irradiance)
            self.history['outdoor_temp'].append(self.outdoor_temp)
            self.history['price'].append(self.price)

            self.step_counter += 1
            self._save_history_to_csv("DataFeeder")
            await super(DataFeederWrapper, self).step(BlockStatus.EXECUTION_STEP_FINISHED)
        except Exception as e:
            error_txt = "Error in step() -> " + str(e)
            logger.error(error_txt)
            await self.send_notify(SimulationPhase.EXECUTE, BlockStatus.ERROR_STEP, error_txt)

    async def finalize(self, status=None, error_text="") -> None:
        logger.debug("Finalizing Data Feeder.")
        self._save_history_to_csv("DataFeeder")
        await super(DataFeederWrapper, self).finalize()

    def _save_history_to_csv(self, filename_prefix: str) -> None:
        try:
            if self.history and any(self.history.values()):
                csv_filename = f"{self.userdata_directory}/{filename_prefix}_history.csv"

                headers = list(self.history.keys())
                columns = list(self.history.values())

                rows = zip_longest(*columns, fillvalue="")

                with open(csv_filename, mode='w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
                    writer.writerows(rows)

                logger.info(f"History successfully saved to {csv_filename} using csv module.")
            else:
                logger.warning("No data found in history to save.")

        except Exception as e:
            logger.error(f"Failed to save CSV: {e}")


if __name__ == '__main__':
    try:
        asyncio.run(main(wrapper=DataFeederWrapper()))
        logger.debug("The main method of the DataFeederWrapper.py gets executed!")
    except KeyboardInterrupt:
        exit(0)