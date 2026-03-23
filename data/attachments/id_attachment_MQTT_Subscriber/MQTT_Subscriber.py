# Author: Xuanhao Mu
# Last update: 05.03.2025
# This module subscribes data from a mosquitto MQTT broker for PROOF.

import time
import json
import paho.mqtt.client as mqtt
import datetime
from sys import exit
import queue
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
log_file_name = f"proof_MQTTSubscriber_{options.local_block_id}.log"
logger = Logger('MQTTSubscriberLogger', handlers=[HandlerType.FILE], logging_dir=options.loggingDir,
                log_file_name=log_file_name, log_level=options.logLevel).get_logger()


class MQTTSubscriber(BaseWrapper):
    def __init__(self, opt=options) -> None:
        print("MQTTSubscriber __init__")
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
        self.timeout = None
        self.cafile_path = None
        self.certfile_path = None
        self.keyfile_path = None
        self.expected_message_count = None  # expected number of messages to receive
        # MQTT Server
        self.client = None

        # MQTT message settings
        self.message_received = False
        self.received_messages = []
        self.message_count = 0
        self.received_messages_list = []
        self.message_queue = queue.Queue()  # Queue to cache received messages


        super(MQTTSubscriber, self).__init__(bwoptions=options)

    async def init(self, status=None, error_text="") -> None:
        try:
            logger.debug("init() -> initializing MQTTSubscriber")
            logger.debug("subscribe mqtt data: from the url '%s', port '%s', topic '%s'" % (self.hostname, self.port, self.topic))

            if self.client_id is None:
                self.client_id = "MQTT_Subscriber_" + str(datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')) + f"_{random.randint(0, 9999):04d}"
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

            if self.timeout is None:
                self.timeout = 1800
                logger.info("Timeout is not provided. Using default timeout: " + str(self.timeout))
            else:
                logger.info("Timeout is provided. Using timeout: " + str(self.timeout))

            if self.expected_message_count is None:
                self.expected_message_count = 1
                logger.info("Expected message count is not provided. Using default count: " + str(self.expected_message_count))
            else:
                logger.info("Expected message count is provided. Using count: " + str(self.expected_message_count))

            self.connected = False
            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
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

        await super(MQTTSubscriber, self).init()

    async def step(self, status=None, error_text="") -> None:
        logger.debug("step() -> subscribe new message")
        start_time = time.time()
        try:
            logger.info("Waiting for message...")
            while not self.message_received:
                current_time = time.time()
                # check if the total timeout is reached
                if current_time - start_time > self.timeout:
                    logger.error("Total timeout reached. Not enough messages received.")
                    break
                try:
                    if not self.message_queue.empty():
                        message = self.message_queue.get_nowait()
                        await self.handle_message(message)
                        self.message_queue.task_done()
                    else:
                        await asyncio.sleep(1)
                except queue.Empty:
                    await asyncio.sleep(1)

            self.received_messages = json.dumps(self.received_messages_list.copy())
            self.received_messages_list = []  # Clear processed messages
            self.message_count = 0  # Reset message count
            self.message_received = False

            await super(MQTTSubscriber, self).step(BlockStatus.EXECUTION_STEP_FINISHED)
        except Exception as e:
            error_txt = "Error in step() -> " + str(e)
            logger.error(error_txt)
            await self.send_notify(SimulationPhase.EXECUTE, BlockStatus.ERROR_INIT, error_txt)

    async def finalize(self, status=None, error_text="") -> None:
        logger.debug("finalize() -> MQTTSubscriber executed the finalize method")
        self.client.loop_stop()  # Stop the loop
        self.client.disconnect()  # Disconnect from the broker
        await super(MQTTSubscriber, self).finalize()

    async def handle_message(self, msg):
        self.message_count += 1
        message = msg.payload.decode()
        self.received_messages_list.append(message)
        logger.info(f"Count: {self.message_count}, Message: {message}")
        # When the number of processed messages reaches the target, set message_received to True
        if self.message_count >= self.expected_message_count:
            logger.info("Received the target number of messages.")
            self.message_received = True

    def on_connect(self, client, userdata, flags, rc, properties=None):
        logger.debug("Connected with result code " + str(rc))
        self.connected = True
        client.subscribe(self.topic)

    def on_message(self, client, userdata, msg, properties=None):
        self.message_queue.put(msg)  # Put the message into the queue


if __name__ == '__main__':
    try:
        logger.debug("The main method of the MQTT_Subscriber.py gets executed!")
        asyncio.run(main(wrapper=MQTTSubscriber()))
    except KeyboardInterrupt:
        exit(0)