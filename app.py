import json, ccxt, os
from flask import Flask, request
app = Flask(__name__)

FTX_API_KEY = os.environ.get('FTX_API_KEY')
FTX_SECRET = os.environ.get('FTX_SECRET')
SUBACCOUNT_NAME = os.environ.get('SUBACCOUNT_NAME')
WEBHOOK_PASSPHRASE = os.environ.get('WEBHOOK_PASSPHRASE')

# get the ftx exchange instance
exchange_id = 'ftx'
exchange_class = getattr(ccxt, exchange_id)
exchange = exchange_class({
    'apiKey': FTX_API_KEY,
    'secret': FTX_SECRET,
    "headers": {
        "FTX-SUBACCOUNT": SUBACCOUNT_NAME,
    }
})

# create function to create order via single json request
def order(symbol, side, amount, type='market', price=None, params={}):
    try:
        #create buy market order
        print("sending order, {} - {} {} {}".format(type, side, amount, symbol))
        order = exchange.create_order(symbol=symbol, side=side, amount=amount, type=type, price=price, params=params)
    except Exception as e:
        print("error: {}".format(e))
        return False
    return order

@app.route("/")
def hello_world():
    return "Hello, World!"

@app.route("/webhook", methods=['POST'])
def webhook():
    # print(request.data)
    data = json.loads(request.data)

    # simple alert authentication
    if data['passphrase'] != WEBHOOK_PASSPHRASE:
        return {
            "code": "error", 
            "message": "invalid passphrase"
        }

    # prevent alerts from other exchanges
    if data['exchange'] != 'FTX':
        return {
            "code": "error", 
            "message": "invalid exchange"
        }

    # change ticker format
    symbol = str(data['ticker']).upper()
    if 'PERP' in symbol:
        symbol = symbol.replace('PERP', '/USD:USD')
    elif 'USD' in symbol:
        symbol = symbol.replace('USD', '/USD')
    else:
        return False

    side = data['strategy']['order_action']
    amount = data['strategy']['order_contracts']
    price = data['strategy']['order_price']
    leverage = 5
    lever_response = exchange.set_leverage(leverage)
    order_response = order(symbol, side, amount, type='limit', price=price)
    print("Placing order... {} - {} {} contracts".format(symbol, side, amount))
    print(order_response)
    print(lever_response)

    if order_response:
        return {
            "code": "success",
            "message": "order executed",
            "info": order_response,
            "leverage": lever_response
        }
    else:
        print('order failed')
        return {
            "code": "error",
            "message": "order failed"
        }