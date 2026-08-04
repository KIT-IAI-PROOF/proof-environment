# Author: Xuanhao Mu
# Last update: 05.03.2025
# This module publishes data to a mosquitto MQTT broker for PROOF.

import time
import json
import paho.mqtt.client as mqtt
import datetime
from sys import exit
import asyncio
import random
from pathlib import Path

from proofcore.base import cliargparser
from proofcore.models.SimulationPhase import SimulationPhase
from proofcore.base.basewrapper import BaseWrapper, main
from proofcore.models.BlockStatus import BlockStatus
from proofcore.util.proofLogging import Logger, HandlerType

options, arguments = cliargparser.parse_known_args()

# Logger
log_file_name = f"proof_MQTTPublisher_{options.local_block_id}.log"
logger = Logger('MQTTPublisherLogger', handlers=[HandlerType.FILE], logging_dir=options.loggingDir,
                log_file_name=log_file_name, log_level=options.logLevel).get_logger()


class MQTTPublisher(BaseWrapper):
    def __init__(self, opt=options) -> None:
        print("MQTTPublisher __init__")
        print("options: ", opt)
        print("===============================================")
        # MQTT Server necessary settings
        self.hostname = ""
        self.port = 0
        self.topic = ""
        # MQTT Server optional settings
        self.username = None
        self.password = None
        self.client_id = None
        self.cafile_path = None
        self.certfile_path = None
        self.keyfile_path = None
        # MQTT Server
        self.client = None
        self.QoS = None
        self.timeout = None

        # MQTT message settings
        self.message = None


        super(MQTTPublisher, self).__init__(bwoptions=options)

    async def init(self, status=None, error_text="") -> None:
        try:
            logger.debug("init() -> initializing MQTTPublisher")
            logger.debug("publish mqtt data to the url '%s', port '%s', topic '%s'" % (self.hostname, self.port, self.topic))

            if self.client_id is None:
                self.client_id = "MQTT_Publisher_" + str(datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')) + f"_{random.randint(0, 9999):04d}"
                logger.info("Client ID is not provided. Using random generated ID: " + self.client_id)
            else:
                logger.info("Client ID is provided. Using client ID: " + self.client_id)

            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=self.client_id)
            logger.info("MQTT client created")

            if self.cafile_path is not None and self.certfile_path is not None and self.keyfile_path is not None:
                self.client.tls_set(ca_certs=Path(self.userdata_directory) / self.cafile_path,
                                    certfile=Path(self.userdata_directory) / self.certfile_path,
                                    keyfile=Path(self.userdata_directory) / self.keyfile_path,
                                    tls_version=mqtt.ssl.PROTOCOL_TLS,
                                    cert_reqs=mqtt.ssl.CERT_REQUIRED)
                logger.info("All TLS certificates are provided, connecting with certificates.")
            else:
                logger.info("Not all TLS certificates are provided, connecting without certificates.")

            if self.username is not None and self.password is not None:
                self.client.username_pw_set(self.username, self.password)
                logger.info("Username and password are provided, connecting with credentials.")
            else:
                logger.info("Username and password are not provided, connecting without credentials.")

            if self.QoS is None:
                self.QoS = 0
                logger.info("QoS is not provided. Using default QoS: " + str(self.QoS))
            elif self.QoS < 0 or self.QoS > 2:
                raise Exception("QoS value is out of range. Please provide a value between 0 and 2.")
            else:
                logger.info("QoS is provided. Using QoS: " + str(self.QoS))

            if self.timeout is None:
                self.timeout = 5
                logger.info("Timeout of publisher is not provided. Using default timeout: " + str(self.timeout))
            else:
                logger.info("Timeout of publisher is provided. Using timeout: " + str(self.timeout))

            self.connected = False
            self.client.on_connect = self.on_connect
            self.client.connect(self.hostname, int(self.port))  # Connect to the broker
            self.client.loop_start()  # Start the loop

            # Wait for the connection to be fully established
            wait_start = time.time()
            while not self.connected:
                if time.time() - wait_start > 10:
                    raise Exception("Connection timeout: could not connect to broker within 10 seconds")
                await asyncio.sleep(0.1)

            logger.info("MQTT client connected")

        except Exception as e:
            error_txt = "Error in init() -> " + str(e)
            logger.error(error_txt)
            await self.send_notify(SimulationPhase.INIT, BlockStatus.ERROR_INIT, error_txt)
            return

        await super(MQTTPublisher, self).init()

    async def step(self, status=None, error_text="") -> None:
        logger.debug("step() -> publish new message")
        try:
            info = self.client.publish(self.topic, payload=self.message, qos=self.QoS)  # Publish the message to the topic
            if not info.wait_for_publish(timeout=self.timeout): # This is a blocking call, which makes a conflict with the asyncio event loop
                logger.warning(f"Message publish confirmation timed out after {self.timeout} seconds")

            await super(MQTTPublisher, self).step(BlockStatus.EXECUTION_STEP_FINISHED)
        except Exception as e:
            error_txt = "Error in step() -> " + str(e)
            logger.error(error_txt)
            await self.send_notify(SimulationPhase.EXECUTE, BlockStatus.ERROR_INIT, error_txt)

    async def finalize(self, status=None, error_text="") -> None:
        logger.debug("finalize() -> MQTTPublisher executed the finalize method")
        self.client.loop_stop()  # Stop the loop
        self.client.disconnect()  # Disconnect from the broker
        await super(MQTTPublisher, self).finalize()

    def on_connect(self, client, userdata, flags, rc, properties=None):
        logger.debug("Connected with result code " + str(rc))
        self.connected = True


if __name__ == '__main__':
    try:
        logger.debug("The main method of the MQTT_Publisher.py gets executed!")
        asyncio.run(main(wrapper=MQTTPublisher()))
    except KeyboardInterrupt:
        exit(0)