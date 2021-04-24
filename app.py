from prometheus_client import start_http_server, Summary, Gauge
import requests
import os
import sys

import logging

import time

logger = logging.getLogger(__name__)


ACCOUNT_UUID = os.getenv("ACCOUNT_UUID", None)
if ACCOUNT_UUID == None:
    logger.error("ACCOUNT_UUID must be set to continue")
    sys.exit(1)

PERSONAL_ACCESS_TOKEN = os.getenv("PERSONAL_ACCESS_TOKEN", None)
if PERSONAL_ACCESS_TOKEN == None:
    logger.error("PERSONAL_ACCESS_TOKEN must be set to continue")
    sys.exit(2)

HTTP_PORT = os.getenv("HTTP_PORT", 9822)
UPDATE_FREQUENCY = os.getenv("UPDATE_FREQUENCY",1800)

def generate_metric_data(key,value):
    unit = value["currency"]

    tmp = Gauge(f"account_{key}_balance",f"{key} Balance in {unit}")
    tmp.set(float(value["minorUnits"])/100)
    return tmp



def metrics():

    headers = {
        "Authorization": f"Bearer {PERSONAL_ACCESS_TOKEN}",
        "accept": "application/json"
        }
    
    r = requests.get(f"https://api.starlingbank.com/api/v2/accounts/{ACCOUNT_UUID}/balance", headers=headers)
    if r.status_code != 200:
        logger.error(f"API did not return OK {r.text}")
        return "Error. - See Logs - "

    data = r.json()
    metric_data = []

    for dataset in data.keys():
        metric_data.append(generate_metric_data(dataset,data[dataset]))
    
    return metric_data

if __name__ == "__main__":
    start_http_server(int(HTTP_PORT))
    gauges = []

    while True:
        gauges = metrics()
        time.sleep(int(UPDATE_FREQUENCY))