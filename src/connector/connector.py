import uuid
import yaml
import json
import datetime
import requests
import socketio

from helpers.helpers import *

def load_config(file_path):
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
    return config

# Assuming the config.yaml file is in the same directory as your Python script
config = load_config('config.yaml')

# Access the configuration values
bearer_token = config['bearer_token']
device_uuid = config['device_uuid']
api_endpoint = config['api_endpoint']

log_file = 'requests.log'

# Set headers
headers = {
    'Authorization': 'bearer ' + bearer_token,
    'Content-Type': 'application/json',
    'x-device-type': 'api',
    'x-device-uuid': device_uuid,
    'x-use-i18n-errors': 'true'
}

def clean_logs():
    with open(log_file, "w") as file:
        file.truncate(0)

def write_log(log_message):
    current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{current_time}] {log_message}\n"
    
    with open(log_file, "a") as file:
        file.write(log_entry)

def api_request(endpoint, method, params=None, payload=None, parse_class=None, verbose=False):
    url = api_endpoint + endpoint
    
    if method == 'GET':
        response = requests.get(url, headers=headers, params=params)
    elif method == 'POST':
        response = requests.post(url, headers=headers, params=params, data=json.dumps(payload))
    else:
        raise ValueError('Invalid HTTP method. Supported methods are GET and POST.')
    
    write_log(method + ' request sent to ' + url + ', headers: ' + json.dumps(headers) + ', params: ' + json.dumps(params) + ', data: ' + json.dumps(payload))

    if response.status_code == 200:
        print('\n######## REQUEST TO ' + endpoint + ' returned code ' + str(response.status_code) + ' ########')
        data = response.json()
        write_log('Got response: ' + json.dumps(data))
        if verbose:
            print({
                'url': url,
                'headers': headers,
                'params': params,
                'payload': payload,
                'response': response
            })
        if parse_class:
            parsed_data = parse_class(data)
            return parsed_data
        else:
            return data
    elif response.status_code == 204:
        print('\n######## REQUEST TO ' + endpoint + ' returned code ' + str(response.status_code) + ' ########')
        data = None
        write_log('Got response: ' + json.dumps(data))
        if verbose:
            print({
                'url': url,
                'headers': headers,
                'params': params,
                'payload': payload,
                'response': response
            })
        if parse_class:
            parsed_data = parse_class(data)
            return parsed_data
        else:
            return data
    else:
        print('Error:', response.text)
        return None

def get_balance():
    balance = api_request('v3/balance', 'GET', parse_class=Balance)
    return balance

def get_rates():
    rates = api_request('v1/exchange/rates-ext', 'GET', parse_class=ExchangeRates)
    return rates

def get_ohlc_data(fromTicker, toTicker, timeframe, mode):
    current_datetime = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    params = {
        'type': 'candle',
        'fromTicker': fromTicker,
        'toTicker': toTicker,
        'tick': timeframe,
        'points': 100,
        'toDate': current_datetime,
        'mode': mode
    }
    ohlc_data = api_request('v2/rates/chart', 'GET', params, parse_class=Ohlc)
    return ohlc_data

def get_tariff_list():
    tariffs = api_request('v3/hodl/tariffs', 'GET', parse_class=TariffList)
    return tariffs

def get_active_orders():
    params = {
        'status': 'OPEN'
    }
    orders = api_request('v3/hodl', 'GET', params, parse_class=OrderList)
    return orders

def get_pending_orders():
    params = {
        'status': 'PENDING'
    }
    orders = api_request('v3/hodl', 'GET', params, parse_class=OrderList)
    return orders

def get_closed_orders():
    params = {
        'limit': 100,
        'offset': 0,
        'status': 'CLOSED'
    }
    orders = api_request('v3/hodl', 'GET', params, parse_class=OrderList)
    return orders

def get_canceled_orders():
    params = {
        'limit': 100,
        'offset': 0,
        'status': 'CANCELED'
    }
    orders = api_request('v3/hodl', 'GET', params, parse_class=OrderList)
    return orders

def get_orders():
    orders = get_closed_orders()
    active_orders = get_active_orders()
    pending_orders = get_pending_orders()
    canceled_orders = get_canceled_orders()
    if orders is not None:
        if active_orders is not None: orders.merge(active_orders)
        if pending_orders is not None: orders.merge(pending_orders)
        if canceled_orders is not None: orders.merge(canceled_orders)
    return orders

def create_market_order(base_ticker, quote_ticker, direction, multiplier, input_amount, input_ticker, tp=None, sl=None):
    current_datetime = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

    # get tariff list and find a tariff for the ticker
    tariff_list = get_tariff_list()
    if tariff_list is not None:
        tariff = tariff_list.search_tariff(base_ticker, quote_ticker, direction)
    else:
        tariff = None

    # get rates and find a current mid price for the ticker
    rates = get_rates()
    if rates is not None:
        rate = rates.search_rate(base_ticker, quote_ticker)
    else:
        rate = None
    
    payload = {
        "date": current_datetime,
        "initial": rate.mid if rate is not None else None,
        "inputAmount": input_amount,
        "inputTicker": input_ticker,
        "multiplier": multiplier,
        "tariffId": tariff.id if tariff is not None else None,
        "requestId" : str(uuid.uuid4())
    }
    if tp is not None: payload['tp'] = tp
    if sl is not None: payload['sl'] = sl
    #print(payload)
    order = api_request('v3/hodl', 'POST', payload=payload, parse_class=OrderAck)
    return order

def cancel_market_order(order_ack):
    current_datetime = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

    rates = get_rates()
    if rates is not None:
        rate = rates.search_rate(order_ack.base_ticker, order_ack.quote_ticker)
    else:
        rate = None
    
    payload = {
        'date': current_datetime,
        'id': order_ack.id,
        'price': rate.mid if rate is not None else None,
        'requestId': str(uuid.uuid4())
    }
    ack = api_request('v3/hodl/closeNow', 'POST', payload=payload, parse_class=CancelMarketAck)
    return ack

