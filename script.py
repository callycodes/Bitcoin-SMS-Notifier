from twilio.rest import Client
from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json
import math
from apscheduler.schedulers.blocking import BlockingScheduler


def distance(a, b):
    if (a == b):
        return 0
    elif (a < 0) and (b < 0) or (a > 0) and (b >= 0):  # fix: b >= 0 to cover case b == 0
        if (a < b):
            return (abs(abs(a) - abs(b)))
        else:
            return -(abs(abs(a) - abs(b)))
    else:
        return math.copysign((abs(a) + abs(b)), b)


account_sid = ''
auth_token = ''
coinmarketurl = ''
coin_api = ''
btc_amount = 0
twilio_to = ''
twilio_from = ''


def load():
    global account_sid, auth_token, coinmarketurl, coin_api, btc_amount, twilio_to, twilio_from
    with open('info.json') as json_file:
        data = json.load(json_file)
        account_sid = data['twilio']['account_sid']
        auth_token = data['twilio']['auth_token']
        twilio_to = data['twilio']['to']
        twilio_from = data['twilio']['from']
        coinmarketurl = data['coinmarketcap']['url']
        coin_api = data['coinmarketcap']['api_key']
        btc_amount = float(data['wallet']['btc_amount'])


load()

client = Client(account_sid, auth_token)

last_worth = 0


def getBTCInfo():
    url = coinmarketurl
    parameters = {
        'id': '1'
    }
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': coin_api,
    }

    session = Session()
    session.headers.update(headers)

    try:
        response = session.get(url, params=parameters)
        data = json.loads(response.text)
        print(data)
        return data
    except (ConnectionError, Timeout, TooManyRedirects) as e:
        print(e)


def getSMSMessage():
    global last_worth
    info = getBTCInfo()
    usd = float(info['data']['1']['quote']['USD']['price'])
    percent = info['data']['1']['quote']['USD']['percent_change_24h']
    btc_worth = float("%.2f" % round((btc_amount * usd), 2))
    last_worth2 = last_worth
    last_worth = btc_worth
    return "BTC Price: $" + str(usd) + " \n24HR Change: " + str(
        percent) + "%" + "\nPortfolio Worth: $" + str(btc_worth) + "\nGrowth: $" + str(
        distance(last_worth2, btc_worth))


def sendSMS():
    message = client.messages.create(
        to=twilio_to,
        from_=twilio_from,
        body=getSMSMessage())

    print("Sent SMS: " + message.sid)


print("BTC Notifier - Running")

scheduler = BlockingScheduler()
scheduler.add_job(sendSMS, 'interval', hours=1)
scheduler.start()
