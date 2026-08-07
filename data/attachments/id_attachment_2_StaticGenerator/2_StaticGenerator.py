import traceback
import asyncio
import subprocess
import csv
from pathlib import Path
from itertools import zip_longest

from proofcore.base import cliargparser
from proofcore.models.SimulationPhase import SimulationPhase
from proofcore.base.basewrapper import BaseWrapper, main
from proofcore.models.BlockStatus import BlockStatus
from proofcore.util.proofLogging import Logger, HandlerType
from sys import exit

options, arguments = cliargparser.parse_known_args()

# Logger
log_file_name = f"proof_StaticGenerator_{options.local_block_id}.log"
logger = Logger('StaticGeneratorLogger', handlers=[HandlerType.FILE], logging_dir=options.loggingDir,
                log_file_name=log_file_name, log_level=options.logLevel).get_logger()


class PVWrapper(BaseWrapper):
    def __init__(self, opt=options) -> None:
        self.irradiance = None
        self.outdoor_temp = None
        #self.use_java = True

        self.pv_power = None

        self.efficiency = 0.18
        self.area = 20.0  # m2

        self.history = {
            'pv_power': [],
            'eff_loss': []
        }
        super(PVWrapper, self).__init__(bwoptions=options)
        logger.info("StaticGenerator initialized.")

    async def init(self, status=None, error_text="") -> None:

        await super(PVWrapper, self).init()

    JAVA_DIR = Path(__file__).resolve().parent / "2_StaticGenerator"
    JAVA_FILE = "PVCalculator.java"
    CLASS_NAME = "PVCalculator"

    # Compile the Java code if necessary. This checks if the .class file exists and is up to date with the .java file.
    def _ensure_compiled(self):
        java_path = self.JAVA_DIR / self.JAVA_FILE
        class_path = self.JAVA_DIR / f"{self.CLASS_NAME}.class"

        if not java_path.exists():
            raise FileNotFoundError(f"Missing {java_path}")

        class_path_exists = class_path.exists()
        class_too_old = java_path.stat().st_mtime > class_path.stat().st_mtime if class_path_exists else True
        needs_compile = not class_path_exists
        #if class_path.exists() and class_too_old:
        #    needs_compile = True

        if needs_compile:
            logger.debug(f"Need to re-compile java (File exists: {class_path_exists}, class_too_old: {class_too_old}):\n{['javac', str(java_path)]}")
            res = subprocess.run(
                ["javac", str(java_path)],
                capture_output=True, text=True,
            )
            if res.returncode != 0:
                raise RuntimeError(f"javac failed: {res.stderr.strip() or res.stdout.strip()}")
    # Run the Java code to calculate PV power and efficiency loss. The Java program should print the results to stdout
    def _run_pv_java(self, irradiance, temp, efficiency, area):
        self._ensure_compiled()
        logger.debug(f"Calling java subprocess:\n{['java', '-cp', str(self.JAVA_DIR), self.CLASS_NAME, str(irradiance), str(temp), str(efficiency), str(area)]}")
        res = subprocess.run(
            ["java", "-cp", str(self.JAVA_DIR), self.CLASS_NAME,
             str(irradiance), str(temp), str(efficiency), str(area)],
            capture_output=True, text=True,
        )
        if res.returncode != 0:
            raise RuntimeError(f"java failed: {res.stderr.strip() or res.stdout.strip()}")

        lines = res.stdout.strip().splitlines()
        power_kw = float(lines[0])
        loss = float(lines[1])
        return power_kw, loss

    async def step(self, status=None, error_text="") -> None:
        try:
            irradiance = self.irradiance
            temp = self.outdoor_temp

            #if self.use_java:
            logger.debug(f"Calling java file with irradiance={irradiance}, temp={temp}, efficiency={self.efficiency}, area={self.area}")
            power_kw, loss = self._run_pv_java(irradiance, temp, self.efficiency, self.area)
            # else:
            #     # virtual Legacy
            #     temp_coeff = 0.005
            #     loss = (temp - 25.0) * temp_coeff
            #     real_efficiency = self.efficiency * (1.0 - loss)
            #     power_watts = irradiance * self.area * real_efficiency
            #     power_kw = max(0.0, power_watts / 1000.0)

            self.pv_power = power_kw

            self.history['pv_power'].append(self.pv_power)
            self.history['eff_loss'].append(loss)

            logger.debug(f"PV Calculation: Irr={irradiance}, Temp={temp} -> Power={power_kw} kW")
            self._save_history_to_csv("StaticGenerator")
            await super(PVWrapper, self).step(BlockStatus.EXECUTION_STEP_FINISHED)
        except Exception as e:
            error_txt = "Error in PV step() -> " + str(e)
            logger.error(error_txt)
            await self.send_notify(SimulationPhase.EXECUTE, BlockStatus.ERROR_STEP, error_txt)

    async def finalize(self, status=None, error_text="") -> None:
        logger.debug("Finalizing PV Model")
        # Saving with csv module ---
        try:
            self._save_history_to_csv("StaticGenerator")
        except Exception as e:
            logger.error(f"Failed to save CSV: {e}")

        await super(PVWrapper, self).finalize()

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
        asyncio.run(main(wrapper=PVWrapper()))
    except KeyboardInterrupt:
        exit(0)
