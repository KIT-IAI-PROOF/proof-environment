import traceback
import asyncio
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
log_file_name = f"proof_Building_{options.local_block_id}.log"
logger = Logger(f'BuildingLogger', handlers=[HandlerType.FILE], logging_dir=options.loggingDir,
                log_file_name=log_file_name, log_level=options.logLevel).get_logger()


class BuildingWrapper(BaseWrapper):
    def __init__(self, opt=options) -> None:
        # --- RC model instead of real building model---
        self.R = 0.8  # [°C/kW]
        self.C = 3.0  # [kWh/°C]

        self.dt = 5.0 / 60.0  # [h]

        self.indoor_temp = None # [°C]
        self.outdoor_temp = None  # [°C]
        self.p_hvac = None  # [kW]

        self.history = {
            'indoor_temp': [],
            'p_hvac_input': []
        }

        super(BuildingWrapper, self).__init__(bwoptions=options)
        logger.debug(f"Building initialized with initial temp {self.indoor_temp}")

    async def init(self, status=None, error_text="") -> None:
        # self.indoor_temp = 28.0
        await super(BuildingWrapper, self).init()
        logger.debug(f"Building init with initial temp {self.indoor_temp}")

    async def step(self, status=None, error_text="") -> None:
        try:
            t_out = self.outdoor_temp
            p_hvac = self.p_hvac

            # --- RC model instead of real building model---
            # Q_loss = (T_out - T_in) / R
            # Q_cool = P_hvac * COP (Assume COP=3)
            heat_loss = (t_out - self.indoor_temp) / self.R
            cooling_energy = p_hvac * 3.0

            delta_temp = (heat_loss - cooling_energy) / self.C * self.dt

            self.indoor_temp += delta_temp
            self.history['indoor_temp'].append(self.indoor_temp)
            self.history['p_hvac_input'].append(p_hvac if p_hvac is not None else 0.0)

            logger.debug(f"Building: T_out={t_out}, HVAC={p_hvac} -> T_in={self.indoor_temp}")
            self._save_history_to_csv("Building")
            await super(BuildingWrapper, self).step(BlockStatus.EXECUTION_STEP_FINISHED)
        except Exception as e:
            error_txt = "Error in Building step() -> " + str(e)
            logger.error(error_txt)
            await self.send_notify(SimulationPhase.EXECUTE, BlockStatus.ERROR_STEP, error_txt)

    async def finalize(self, status=None, error_text="") -> None:
        logger.debug("Finalizing Building Model")
        # Saving with csv module ---
        try:
            self._save_history_to_csv("Building")
        except Exception as e:
            logger.error(f"Failed to save CSV: {e}")
        await super(BuildingWrapper, self).finalize()

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
        asyncio.run(main(wrapper=BuildingWrapper()))
    except KeyboardInterrupt:
        exit(0)