from prometheus_client import start_http_server, Summary, Gauge
import requests
import os
import sys

import logging

import time

logger = logging.getLogger(__name__)

# split list of personal access tokens into an array
STARLING_BANK_TOKEN_LIST=os.getenv("STARLING_BANK_TOKEN_LIST", None)
if STARLING_BANK_TOKEN_LIST == None:
    logger.error("STARLING_BANK_TOKEN_LIST must be set to continue")
    sys.exit(2)

STARLING_BANK_TOKEN_ARRAY=STARLING_BANK_TOKEN_LIST.split(',')

# define key constants
HTTP_PORT = os.getenv("HTTP_PORT", 9822)
UPDATE_FREQUENCY = os.getenv("UPDATE_FREQUENCY",1800)
ACCOUNT_LABELS=['AccountNumber', 'AccountName']
SPACE_LABELS=['AccountNumber', 'AccountName', 'SpaceUid', 'SpaceName']

# define account gauges
cleared_balance = Gauge("starling_account_cleared_balance", "Starling Cleared Balance", ACCOUNT_LABELS)
effective_balance = Gauge("starling_account_effective_balance", "Starling Effective Balance", ACCOUNT_LABELS)
pending_transactions = Gauge("starling_account_pending_transactions", "Starling Pending Transactions", ACCOUNT_LABELS)
accepted_overdraft = Gauge("starling_account_accepted_overdraft", "Starling Overdraft", ACCOUNT_LABELS)
amount = Gauge("starling_account_amount", "Starling Account Balance", ACCOUNT_LABELS)

# define space gauges
account_space_balance = Gauge("starling_account_space_balance", "Starling Account Space Balance", SPACE_LABELS)

###############################################################################
# define metrics function
def metrics():

    metrics=[]

    # loop through each access token
    for PERSONAL_ACCESS_TOKEN in STARLING_BANK_TOKEN_ARRAY:

        THIS_ACCOUNT=[]

        # define headers
        headers = {
            "Authorization": f"Bearer {PERSONAL_ACCESS_TOKEN}",
            "accept": "application/json"
            }

        # get account for this personal access token
        r = requests.get(f"https://api.starlingbank.com/api/v2/accounts", headers=headers)
        if r.status_code != 200:
            logger.error(f"API did not return OK {r.text}")
            return "Error. - See Logs - "

        # extract account UID and name
        data = r.json()
        THIS_ACCOUNT_UID = data['accounts'][0]['accountUid']
        THIS_ACCOUNT_NAME = data['accounts'][0]['name']

        # get account identifiers
        r = requests.get(f"https://api.starlingbank.com/api/v2/accounts/{THIS_ACCOUNT_UID}/identifiers", headers=headers)
        if r.status_code != 200:
            logger.error(f"API did not return OK {r.text}")
            return "Error. - See Logs - "

        # extract account number
        data = r.json()
        THIS_ACCOUNT_NUMBER = data['accountIdentifier']

        # get account balances
        r = requests.get(f"https://api.starlingbank.com/api/v2/accounts/{THIS_ACCOUNT_UID}/balance", headers=headers)
        if r.status_code != 200:
            logger.error(f"API did not return OK {r.text}")
            return "Error. - See Logs - "

        # extract and calculate balances
        data = r.json()
        cleared_balance_value = float(data['clearedBalance']['minorUnits'])/100.0
        effective_balance_value = float(data['effectiveBalance']['minorUnits'])/100.0
        pending_transactions_value = float(data['pendingTransactions']['minorUnits'])/100.0
        accepted_overdraft_value = float(data['acceptedOverdraft']['minorUnits'])/100.0
        amount_value = float(data['amount']['minorUnits'])/100.0

        # set gauge values
        cleared_balance.labels(AccountNumber=THIS_ACCOUNT_NUMBER, AccountName=THIS_ACCOUNT_NAME).set(cleared_balance_value)
        effective_balance.labels(AccountNumber=THIS_ACCOUNT_NUMBER, AccountName=THIS_ACCOUNT_NAME).set(effective_balance_value)
        pending_transactions.labels(AccountNumber=THIS_ACCOUNT_NUMBER, AccountName=THIS_ACCOUNT_NAME).set(accepted_overdraft_value)
        accepted_overdraft.labels(AccountNumber=THIS_ACCOUNT_NUMBER, AccountName=THIS_ACCOUNT_NAME).set(pending_transactions_value)
        amount.labels(AccountNumber=THIS_ACCOUNT_NUMBER, AccountName=THIS_ACCOUNT_NAME).set(amount_value)

        # append gauges to metrics array
        metrics.append(cleared_balance)
        metrics.append(effective_balance)
        metrics.append(pending_transactions)
        metrics.append(accepted_overdraft)
        metrics.append(amount)

        # get account spaces
        r = requests.get(f"https://api.starlingbank.com/api/v2/account/{THIS_ACCOUNT_UID}/spaces", headers=headers)
        if r.status_code != 200:
            logger.error(f"API did not return OK {r.text}")
            return "Error. - See Logs - "

        # extract space details
        data = r.json()

        # loop through each space (if any)
        for THIS_SPACE in data["savingsGoals"]:

            # extract space balance
            space_balance_value = float(THIS_SPACE['totalSaved']['minorUnits'])/100.0

            # set gauge value and append to metrics array
            account_space_balance.labels(AccountNumber=THIS_ACCOUNT_NUMBER, AccountName=THIS_ACCOUNT_NAME, SpaceUid=THIS_SPACE['savingsGoalUid'], SpaceName=THIS_SPACE['name']).set(space_balance_value)
            metrics.append(account_space_balance)
            
    # return the metrics array
    return [metrics]

###############################################################################
if __name__ == "__main__":

    # start the http serve
    start_http_server(int(HTTP_PORT))
    
    # define the gauges array
    gauges = []

    # loop forever
    while True:

        # call the function to update the gauges
        gauges = metrics()

        # sleep until time for next update
        time.sleep(int(UPDATE_FREQUENCY))
