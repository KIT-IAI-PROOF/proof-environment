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
log_file_name = f"proof_Controller_{options.local_block_id}.log"
logger = Logger(f'ControllerLogger', handlers=[HandlerType.FILE], logging_dir=options.loggingDir,
                log_file_name=log_file_name, log_level=options.logLevel).get_logger()


class ControllerWrapper(BaseWrapper):
    def __init__(self, opt=options) -> None:
        # --- PID Controller Parameters ---
        # Output(kW) = Kp * Error(°C) + Ki * Integral(°C·h) + Kd * Derivative(°C/h)
        self.Kp = 4  # [kW/°C]
        self.Ki = 0.15  # [kW/(°C·h)]
        self.Kd = 0.5  # [kW·h/°C]

        # --- State Variables for PID ---
        self.prev_error = 0.0  # [°C]
        self.integral = 0.0  # [°C·h]
        self.dt = 5.0 / 60.0  # [h]

        # --- Constraints ---
        self.max_power = 10.0  # [kW]
        self.deadband = 0.2  # [°C]

        self.target_temp_base = 24.0  # [°C]
        self.pv_threshold = 2.0  # [kW]
        self.price_threshold = 1.0  # [$/kWh]

        self.indoor_temp = None  # [°C]
        self.price = None  # [$/kWh]
        self.pv_power = None  # [kW]
        self.p_hvac = 0.0  # [kW]

        self.history = {
            'target_temp': [],
            'error': [],
            'hvac_cmd': []
        }

        super(ControllerWrapper, self).__init__(bwoptions=options)
        logger.info("Controller initialized with initial temp {self.indoor_temp}")

    async def init(self, status=None, error_text="") -> None:

        await super(ControllerWrapper, self).init()

    """
    -----------------------------------------------------------------------
    CONTROL STRATEGY DESCRIPTION
    -----------------------------------------------------------------------
    This controller operates on two layers to optimize energy usage while 
    maintaining thermal comfort.

    Tracking Control (PID Algorithm)
    - Calculates the required HVAC power to minimize the error between 
      'Indoor Temp' and 'Target Temp'.
    - Implements a 'Deadband' to prevent actuator oscillation (short-cycling) 
      when the temperature is close enough to the target.
    - Includes 'Anti-windup' to prevent the integral term from accumulating 
      excessively when the HVAC is saturated (max power).
    -----------------------------------------------------------------------
    """
    async def step(self, status=None, error_text="") -> None:
        try:
            # --- 1. Read Inputs ---
            t_in = self.indoor_temp
            price = self.price
            pv = self.pv_power
            target_temp = self.target_temp_base  # Default comfort temp

            if pv is not None and pv > self.pv_threshold:
                target_temp -= 1.0  # 目标变为 26.0°C (更凉快)
                logger.debug(f"High PV detected ({pv:.2f} kW). Lowering target temp to {target_temp}")

            elif price is not None and price > self.price_threshold:
                target_temp += 1.5  # 目标变为 28.5°C (稍微热一点，但省电)
                logger.debug(f"High Price detected ({price:.2f} $/kWh). Raising target temp to {target_temp}")

            # === PID Tracking ===
            error = t_in - target_temp

            # Deadband check: if error is very small, do nothing to save equipment life
            if abs(error) < self.deadband:
                hvac_power = 0.0
                # Optional: Reset integral when inside deadband to avoid overshoot later
                self.integral = 0.0
            else:
                # PID Calculation
                self.integral += error * self.dt
                derivative = (error - self.prev_error) / self.dt

                # Standard PID formula
                output = (self.Kp * error) + (self.Ki * self.integral) + (self.Kd * derivative)

                # Anti-windup & Saturation (Clamp 0 to Max Power)
                if output > self.max_power:
                    hvac_power = self.max_power
                    # Prevent integral from growing if we are already maxed out
                    self.integral -= error * self.dt
                elif output < 0:
                    hvac_power = 0.0
                    # Prevent integral from growing (negatively) if we are at 0
                    self.integral -= error * self.dt
                else:
                    hvac_power = output

            self.history['target_temp'].append(target_temp)
            self.history['error'].append(error)
            self.history['hvac_cmd'].append(hvac_power)
            # Update state for next step
            self.prev_error = error
            self.p_hvac = hvac_power

            logger.debug(f"Controller Decision: Price={price}, PV={pv}, T_in={t_in} -> HVAC={hvac_power}")
            self._save_history_to_csv("Controller")
            await super(ControllerWrapper, self).step(BlockStatus.EXECUTION_STEP_FINISHED)
        except Exception as e:
            error_txt = "Error in Controller step() -> " + str(e)
            logger.error(error_txt)
            await self.send_notify(SimulationPhase.EXECUTE, BlockStatus.ERROR_STEP, error_txt)

    async def finalize(self, status=None, error_text="") -> None:
        logger.debug("Finalizing Controller Controller")
        # Saving with csv module ---
        try:
            self._save_history_to_csv("Controller")

        except Exception as e:
            logger.error(f"Failed to save CSV: {e}")

        await super(ControllerWrapper, self).finalize()

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
        asyncio.run(main(wrapper=ControllerWrapper()))
    except KeyboardInterrupt:
        exit(0)