from flask import Flask
from flask_caching import Cache

import requests
import os
import sys

import logging

logger = logging.getLogger(__name__)


config = {
    "DEBUG": True,          # some Flask specific configs
    "CACHE_TYPE": "SimpleCache",  # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 1800
}

app = Flask(__name__)

app.config.from_mapping(config)
cache = Cache(app)


ACCOUNT_UUID = os.getenv("ACCOUNT_UUID", None)
if ACCOUNT_UUID == None:
    logger.error("ACCOUNT_UUID must be set to continue")
    sys.exit(1)

PERSONAL_ACCESS_TOKEN = os.getenv("PERSONAL_ACCESS_TOKEN", None)
if PERSONAL_ACCESS_TOKEN == None:
    logger.error("PERSONAL_ACCESS_TOKEN must be set to continue")
    sys.exit(2)

CURRENCY_CODE = os.getenv("CURRENCY_CODE", "gbp")

def generateMetricData(key,value):
    template = f"""
# HELP account_{key}_balance {key}-Account Balance in GBP.
# TYPE account_{key}_balance gauge
# UNIT account_{key}_balance {value["currency"]}
account_{key}_balance {float(value["minorUnits"])/100}"""
    return template

@app.route('/metrics')
@cache.cached(timeout=int(config['CACHE_DEFAULT_TIMEOUT'])-1 )
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
        metric_data.append(generateMetricData(dataset,data[dataset]))
    
    return "".join(metric_data)

