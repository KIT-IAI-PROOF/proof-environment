# PROOF Installation
This page describes the installation of PROOF.
## Docker
Necessary requirement to run PROOF is the usage of docker. To install docker and to see more information about docker, please follow the instructions on the docker homepage: [www.docker.com](https://www.docker.com/). Alternatively, you can install docker by using the command line and the package sources for your corresponding operations system distribution.
## Get proof-environment
To install PROOF, move to the repository [proof-environment](https://github.com/KIT-IAI-PROOF/proof-environment) and clone the repository to your local file system. We recommend creating a PROOF directory for this purpose. To clone the repository using a cli, make sure you have **git** installed on your local machine. Alternatively, you can download the zip-file of proof-environment.
## Start PROOF
To start PROOF, navigate to the following folder within proof-environment:
```
cd proof-environment/docker
```
Afterwards, start PROOF using the compose file in the docker folder:
```
docker compose up
```
PROOF will take a few moments to be started properly. Thus, you can access the PROOF graphical user interface by opening a new browser window/tab and type the following in the URL address bar:
```
localhost:80
```
Due to caching behaviour in some browsers, we **strongly recommend** opening the PROOF UI in a **private browser window** at this moment.

To access the workflow creation editor, the credentials to be used are test/test.
