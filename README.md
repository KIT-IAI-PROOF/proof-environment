# PROOF 
The complete documentation can be found at [https://kit-iai-proof.github.io](https://kit-iai-proof.github.io).

## Execution with Docker
The Docker environment (Docker engine) must be installed on your host system. 

To install docker and to see more information about docker, please follow the instructions on the docker homepage: [www.docker.com](https://www.docker.com/). Alternatively, you can install docker by using the command line and the package sources for your corresponding operations system distribution.

**Windows:** Follow the official [docker documentation](https://docs.docker.com/desktop/setup/install/windows-install/#install-docker-desktop-on-windows).

Other required components are provided via Docker images.

## Installation
Follow these steps to start and run PROOF.

## Get proof-environment
To install PROOF, move to the repository [proof-environment](https://github.com/KIT-IAI-PROOF/proof-environment) and clone the repository to your local file system. We recommend creating a PROOF directory for this purpose. To clone the repository using a cli, make sure you have **git** installed on your local machine. Alternatively, you can download the zip-file of proof-environment.

## Download the worker image (optional)
Starting with version 1.1.0, PROOF automatically downloads missing Docker images when needed. However, you can optionally download the [proof-worker-python image](https://github.com/orgs/KIT-IAI-PROOF/packages/container/package/proof-worker-python) in advance to speed up the first execution:
```
docker pull ghcr.io/kit-iai-proof/proof-worker-python:1.2.0
```

## Start and stop PROOF
To **start PROOF**, simply use the startPROOF script in the proof-environment directory:
```
./startPROOF
```
**Windows:** Ensure to have the **Docker Desktop App** running. Start PROOF using the startPROOF.bat file.

PROOF will take a few moments to be started properly. Thus, you can access the PROOF graphical user interface by opening a new browser window/tab and type the following in the URL address bar:
```
localhost
```
Due to caching behaviour in some browsers, we **strongly recommend** opening the PROOF UI in a **private browser window** at this moment.

To access the workflow creation editor, the **credentials** to be used are *proof/proof*.

To **stop PROOF**, simply use the stopPROOF script in the proof-environment directory:
```
./stopPROOF
```
**Windows:** Stop PROOF using the stopPROOF.bat file.

## Data exchange
Data exchange with PROOF works via the `proof-environment/data` folder structure:

- **`userdata/`**: Directory for user-managed files that can be accessed by workflow blocks (e.g., *FileReader* block)
- **`attachments/`**: Directory for workflow-specific attachments and configuration files
  - Uploaded attachment files are stored here, organized by their unique attachment ID.
- **`executions/`**: Directory for execution-specific data and logs
  - Execution logs are stored in subdirectories named by execution ID as specified in the docker-compose file.

Files placed in the `userdata` folder can be referenced in your workflows for reading and writing operations.

## Test your installation
To test your installation, you can use the workflow *FileReader-to-FileWriter*. It contains two blocks: the *FileReader* which reads a file given as input parameter and provides the next line each step and the *FileWriter* which receives data and appends it to the file which name is given as an input parameter (e.g. *out.txt*).

When you see that the execution has the status SHUT_DOWN, you can check the contents of the output file (e.g. *out.txt*) which should be the same as the input file for this demo workflow. This can be done via console:
```
cd proof-environment/data/userdata
cat out.txt
```
