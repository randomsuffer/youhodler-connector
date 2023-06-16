from connector.connector import *
from helpers.helpers import *
import talib as ta

print('hello')

clean_logs()

balance = get_balance()
if balance is not None: balance.print()

rates = get_rates()
if rates is not None: rates.print()

ohlc_data = get_ohlc_data('btc', 'usdt', '5m', 'bid')
if ohlc_data is not None: ohlc_data.print()

tariff_list = get_tariff_list()
if tariff_list is not None: tariff_list.print()

orders = get_orders()
if orders is not None: orders.print()

order_ack = create_market_order('btc', 'usdt', 'long', 4, 20, 'usdt')
if order_ack is not None: order_ack.print()

active_orders = get_active_orders()
if active_orders is not None: active_orders.print()

cancel_ack = cancel_market_order(order_ack)
if cancel_ack is not None: cancel_ack.print()
