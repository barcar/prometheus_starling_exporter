from prometheus_client import start_http_server, Summary, Gauge
import requests
import os
import sys

import logging

import time

logger = logging.getLogger(__name__)

STARLING_BANK_TOKEN_LIST=os.getenv("STARLING_BANK_TOKEN_LIST", None)
if STARLING_BANK_TOKEN_LIST == None:
    logger.error("STARLING_BANK_TOKEN_LIST must be set to continue")
    sys.exit(2)

STARLING_BANK_TOKEN_ARRAY=STARLING_BANK_TOKEN_LIST.split(',')

HTTP_PORT = os.getenv("HTTP_PORT", 9822)
UPDATE_FREQUENCY = os.getenv("UPDATE_FREQUENCY",1800)

ACCOUNT_LABELS=['AccountUid', 'AccountName']

cleared_balance = Gauge("starling_account_cleared_balance", "Starling Cleared Balance", ACCOUNT_LABELS)
effective_balance = Gauge("starling_account_effective_balance", "Starling Effective Balance", ACCOUNT_LABELS)
pending_transactions = Gauge("starling_account_pending_transactions", "Starling Pending Transactions", ACCOUNT_LABELS)
accepted_overdraft = Gauge("starling_account_accepted_overdraft", "Starling Overdraft", ACCOUNT_LABELS)
amount = Gauge("starling_account_amount", "Starling Account Balance", ACCOUNT_LABELS)

SPACE_LABELS=['AccountUid', 'AccountName', 'SpaceUid', 'SpaceName']

account_space_balance = Gauge("starling_account_space_balance", "Starling Account Space Balance", SPACE_LABELS)

def metrics():

    metrics=[]

    for PERSONAL_ACCESS_TOKEN in STARLING_BANK_TOKEN_ARRAY:

        THIS_ACCOUNT=[]

        headers = {
            "Authorization": f"Bearer {PERSONAL_ACCESS_TOKEN}",
            "accept": "application/json"
            }

        r = requests.get(f"https://api.starlingbank.com/api/v2/accounts", headers=headers)
        if r.status_code != 200:
            logger.error(f"API did not return OK {r.text}")
            return "Error. - See Logs - "

        data = r.json()
        THIS_ACCOUNT_UID = data['accounts'][0]['accountUid']
        THIS_ACCOUNT_NAME = data['accounts'][0]['name']

        headers = {
            "Authorization": f"Bearer {PERSONAL_ACCESS_TOKEN}",
            "accept": "application/json"
            }

        r = requests.get(f"https://api.starlingbank.com/api/v2/accounts/{THIS_ACCOUNT_UID}/balance", headers=headers)
        if r.status_code != 200:
            logger.error(f"API did not return OK {r.text}")
            return "Error. - See Logs - "

        data = r.json()

        cleared_balance_value = float(data['clearedBalance']['minorUnits'])/100.0
        effective_balance_value = float(data['effectiveBalance']['minorUnits'])/100.0
        pending_transactions_value = float(data['pendingTransactions']['minorUnits'])/100.0
        accepted_overdraft_value = float(data['acceptedOverdraft']['minorUnits'])/100.0
        amount_value = float(data['amount']['minorUnits'])/100.0

        cleared_balance.labels(AccountUid=THIS_ACCOUNT_UID, AccountName=THIS_ACCOUNT_NAME).set(cleared_balance_value)
        effective_balance.labels(AccountUid=THIS_ACCOUNT_UID, AccountName=THIS_ACCOUNT_NAME).set(effective_balance_value)
        pending_transactions.labels(AccountUid=THIS_ACCOUNT_UID, AccountName=THIS_ACCOUNT_NAME).set(accepted_overdraft_value)
        accepted_overdraft.labels(AccountUid=THIS_ACCOUNT_UID, AccountName=THIS_ACCOUNT_NAME).set(pending_transactions_value)
        amount.labels(AccountUid=THIS_ACCOUNT_UID, AccountName=THIS_ACCOUNT_NAME).set(amount_value)

        metrics.append(cleared_balance)
        metrics.append(effective_balance)
        metrics.append(pending_transactions)
        metrics.append(accepted_overdraft)
        metrics.append(amount)

        r = requests.get(f"https://api.starlingbank.com/api/v2/account/{THIS_ACCOUNT_UID}/spaces", headers=headers)
        if r.status_code != 200:
            logger.error(f"API did not return OK {r.text}")
            return "Error. - See Logs - "

        data = r.json()

        for THIS_SPACE in data["savingsGoals"]:

            space_balance_value = float(THIS_SPACE['totalSaved']['minorUnits'])/100.0

            account_space_balance.labels(AccountUid=THIS_ACCOUNT_UID, AccountName=THIS_ACCOUNT_NAME, SpaceUid=THIS_SPACE['savingsGoalUid'], SpaceName=THIS_SPACE['name']).set(space_balance_value)
            metrics.append(account_space_balance)
            
    return [metrics]

if __name__ == "__main__":
    start_http_server(int(HTTP_PORT))
    gauges = []

    while True:
        gauges = metrics()
        time.sleep(int(UPDATE_FREQUENCY))
