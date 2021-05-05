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

cleared_balance = Gauge("starling_account_cleared_balance", "Starling Cleared Balance")
effective_balance = Gauge("starling_account_effective_balance", "Starling Effective Balance")
pending_transactions = Gauge("starling_account_pending_transactions", "Starling Pending Transactions")
accepted_overdraft = Gauge("starling_account_accepted_overdraft", "Starling Overdraft")
amount = Gauge("starling_account_amount", "Starling Account Balance")

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

    
    cleared_balance_value = float(data['clearedBalance']['minorUnits'])/100.0
    effective_balance_value = float(data['effectiveBalance']['minorUnits'])/100.0
    pending_transactions_value = float(data['pendingTransactions']['minorUnits'])/100.0
    accepted_overdraft_value = float(data['acceptedOverdraft']['minorUnits'])/100.0
    amount_value = float(data['amount']['minorUnits'])/100.0

    cleared_balance.set(cleared_balance_value)
    cleared_balance.set(effective_balance_value)
    cleared_balance.set(accepted_overdraft_value)
    cleared_balance.set(pending_transactions_value)
    cleared_balance.set(amount_value)

    return [cleared_balance]

if __name__ == "__main__":
    start_http_server(int(HTTP_PORT))
    gauges = []

    while True:
        gauges = metrics()
        time.sleep(int(UPDATE_FREQUENCY))