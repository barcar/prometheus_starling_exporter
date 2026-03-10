You probably shouldn't use this unless you know what you're doing. 

You need to have a Starling Developer Account, and have a Personal Access Token for each account you wish to export.

Generate the Personal Access Token with the following permissions:
* account:read
* account-identifier:read
* account-list:read
* balance:read
* savings-goal:read
* space:read

Run the docker container with the following environment variable containing a comma separated list of Personal Access Tokens
* STARLING_BANK_TOKEN_LIST

Fetch the metrics from 127.0.0.1:9822

Docker Hub: https://hub.docker.com/r/devopstom/prometheus-starling-exporter

![Docker Cloud Build Status](https://img.shields.io/docker/cloud/build/devopstom/prometheus-starling-exporter)
![Docker Pulls](https://img.shields.io/docker/pulls/devopstom/prometheus-starling-exporter)
