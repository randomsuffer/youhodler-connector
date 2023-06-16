from datetime import datetime
import pandas as pd

class Wallet:
    def __init__(self, data):
        self.amount = float(data.get('amount', 0))
        self.ticker = data.get('ticker')
        self.versions = data.get('versions', [])
        self.address = data.get('address')
        self.create_enabled = bool(data.get('createEnabled', False))
        self.deposit_enabled = bool(data.get('depositEnabled', False))
        self.withdraw_enabled = bool(data.get('withdrawEnabled', False))
        self.loan_enabled = bool(data.get('loanEnabled', False))
        self.turbo_enabled = bool(data.get('turboEnabled', False))
        self.hodl_enabled = bool(data.get('hodlEnabled', False))
        self.market_enabled = bool(data.get('marketEnabled', False))
        self.chart_enabled = bool(data.get('chartEnabled', False))
        self.visible = bool(data.get('visible', False))
        self.products = data.get('products', [])
        self.hodls_input_amount = float(data.get('hodlsInputAmount', 0))
        self.duals_input_amount = float(data.get('dualsInputAmount', 0))
        self.loans_collateral_amount = float(data.get('loansCollateralAmount', 0))
        self.amount_for_savings = float(data.get('amountForSavings', 0))
        self.capital = data.get('capital', {})
        self.tags = data.get('tags', [])

    def print(self):
        print(f"{self.ticker.upper()}: {self.amount}")


class Balance:
    def __init__(self, data):
        self.total_capital_usd = data['totalCapital']['usd']
        self.wallets = []
        for wallet_data in data['wallets']:
            wallet = Wallet(wallet_data)
            self.wallets.append(wallet)

    def print(self):
        print(f"\nTotal Capital (USD): {self.total_capital_usd}")
        print("Wallets:")
        for wallet in self.wallets:
            if wallet.amount > 0: wallet.print()
        print()

class Rate:
    def __init__(self, data, base_ticker, quote_ticker):
        self.base_ticker = base_ticker
        self.quote_ticker = quote_ticker
        self.ticker = f"{self.base_ticker}/{self.quote_ticker}"
        self.mid = float(data.get('rate', None)) if data.get('rate') is not None else None
        self.ask = float(data.get('ask', None)) if data.get('ask') is not None else None
        self.bid = float(data.get('bid', None)) if data.get('bid') is not None else None
        self.diff24h = float(data.get('diff24h', None)) if data.get('diff24h') is not None else None

    def print(self):
        print(f"{self.ticker.upper()}, Ask: {self.ask}, Bid: {self.bid}, Mid: {self.mid}")

class ExchangeRates:
    def __init__(self, data):
        self.rates = []
        for parent_key, parent_value in data.items():
            for child_key, child_value in parent_value.items():
                rate = Rate(child_value, parent_key, child_key)
                self.rates.append(rate)

    def search_rate(self, base_ticker, quote_ticker):
        for rate in self.rates:
            if rate.base_ticker == base_ticker and rate.quote_ticker == quote_ticker:
                return rate
        return None

    def print(self):
        print('\nRates:')
        for rate in self.rates:
            rate.print()

class Candlestick:
    def __init__(self, data):
        self.date = datetime.strptime(data['date'], "%Y-%m-%dT%H:%M:%S.%fZ")
        self.open = float(data['open'])
        self.high = float(data['high'])
        self.low = float(data['low'])
        self.close = float(data['close'])
        self.forced = bool(data.get('forced', False))

    def print(self):
        print(f"{self.date}, O: {self.open}, H: {self.high}, L: {self.low}, C: {self.close}")

class Ohlc:
    def __init__(self, data):
        self.candlesticks = [Candlestick(item) for item in data]
        self.candlesticks.sort(key=lambda x: x.date)
    
    def to_dataframe(self):
        data = {
            'Date': [candlestick.date for candlestick in self.candlesticks],
            'Open': [candlestick.open for candlestick in self.candlesticks],
            'High': [candlestick.high for candlestick in self.candlesticks],
            'Low': [candlestick.low for candlestick in self.candlesticks],
            'Close': [candlestick.close for candlestick in self.candlesticks]
        }
        df = pd.DataFrame(data)
        return df
    
    def print(self):
        print('\nCandlesticks:')
        for candlestick in self.candlesticks:
            candlestick.print()

class Tariff:
    def __init__(self, data):
        self.id = data.get('id')
        self.base_ticker = data.get('baseTicker')
        self.quote_ticker = data.get('quoteTicker')
        self.min_multiplier = int(data.get('minMultiplier'))
        self.max_multiplier = int(data.get('maxMultiplier'))
        self.min_volume = float(data.get('minVolume'))
        self.max_volume = float(data.get('maxVolume'))
        self.allowed_input_tickers = data.get('allowedInputTickers')
        self.is_enabled = bool(data.get('isEnabled'))
        self.direction = "short" if bool(data.get('isShort')) else "long"
        self.trigger_price_distance_max = float(data.get('triggerPriceDistanceMax'))
        self.pending_order_disabled = bool(data.get('pendingOrderDisabled'))
        self.day_off = bool(data.get('dayOff'))
        self.days_off = data.get('daysOff')
        self.trading_mode = data.get('tradingMode')
    
    def print(self):
        print(f"{self.base_ticker.upper()}/{self.quote_ticker.upper()} {self.direction}: x{self.min_multiplier}–{self.max_multiplier}, volume {self.min_volume} – {self.max_volume}")

class TariffList:
    def __init__(self, data):
        self.tariffs = [Tariff(item) for item in data]
    
    def search_tariff(self, base_ticker, quote_ticker, direction):
        for tariff in self.tariffs:
            if (
                tariff.base_ticker == base_ticker
                and tariff.quote_ticker == quote_ticker
                and tariff.direction == direction
            ):
                return tariff
        return None
    
    def print(self):
        print('\nTariffs:')
        for tariff in self.tariffs:
            tariff.print()

class Order:
    def __init__(self, data):
        self.id = data.get('id')
        self.accountId = data.get('accountId')
        self.direction = "short" if bool(data.get('isShort')) else "long"
        self.multiplier = int(data.get('multiplier'))
        self.input_ticker = data.get('inputTicker')
        self.base_ticker = data.get('baseTicker')
        self.quote_ticker = data.get('quoteTicker')
        self.input_amount = float(data.get('inputAmount'))
        self.output_amount = float(data.get('outputAmount')) if data.get('outputAmount') else None
        self.initial_price = float(data.get('initialPrice'))
        self.mc_price = float(data.get('mcPrice'))
        self.sl_price = float(data.get('slPrice')) if data.get('slPrice') else None
        self.ftp_price = float(data.get('ftpPrice'))
        self.tp_price = float(data.get('tpPrice'))
        self.closed_price = float(data.get('closedPrice')) if data.get('closedPrice') else None
        self.closed = data.get('closed')
        self.status = data.get('status')
        self.reason = data.get('reason')
        self.started_at = datetime.strptime(data.get('startedAt'), '%Y-%m-%dT%H:%M:%S.%fZ') if data.get('startedAt') else None
        self.finished_at = datetime.strptime(data.get('finishedAt'), '%Y-%m-%dT%H:%M:%S.%fZ') if data.get('finishedAt') else None
        if(data.get('status') == 'CLOSED'):
            self.profit = float(data.get('closed').get('profit'))
            self.profit_percent = float(data.get('closed').get('percent')) * 100 - 100
        if(data.get('status') == 'OPEN'):
            self.profit = float(data.get('closeCalculate').get('profit'))
            self.profit_percent = float(data.get('closeCalculate').get('percent')) * 100 - 100
        self.trigger_price = float(data.get('triggerPrice'))
        self.order_type = data.get('orderType')
    
    def print(self):
        print(f"\nOrder {self.id} {self.status}:\n{self.base_ticker.upper()}/{self.quote_ticker.upper()} {self.direction} x{self.multiplier} @ {self.initial_price}, input: {self.input_amount} {self.input_ticker.upper()}, profit: {self.profit} {self.input_ticker.upper()} ({round(self.profit_percent, 2)}%)") 

class OrderList:
    def __init__(self, data):
        self.orders = [Order(item) for item in data.get('rows')]
    
    def merge(self, other):
        self.orders.extend(other.orders)

    def get_active_orders(self):
        orders = []
        for order in self.orders:
            if order.status == "OPEN" or order.status == "PENDING":
                orders.append(order)
        return orders

    def get_closed_orders(self):
        orders = []
        for order in self.orders:
            if order.status == "CLOSED" or order.status == "CANCELED":
                orders.append(order)
        return orders
    
    def print(self):
        print('\nOrders:')
        for order in self.orders:
            order.print()

class OrderAck:
    def __init__(self, data):
        self.id = data.get('id')
        self.direction = "short" if bool(data.get('isShort')) else "long"
        self.base_ticker = data.get('baseTicker')
        self.quote_ticker = data.get('quoteTicker')
        self.input_amount = float(data.get('inputAmount', 0))
        self.input_ticker = data.get('inputTicker')
        self.status = data.get('status')
        self.multiplier = int(data.get('multiplier', 0))
        self.client_initial_price = float(data.get('clientInitialPrice', 0))
        self.client_created_at = datetime.strptime(data.get('clientCreatedAt'), '%Y-%m-%dT%H:%M:%S.%fZ') if data.get('clientCreatedAt') else None
        self.tp = float(data.get('tpPrice', 0))
        self.sl = float(data.get('slPrice')) if data.get('slPrice') else None

    def print(self):
        print(f"\nOrder acknowledgement {self.id} {self.status}:\n{self.base_ticker.upper()}/{self.quote_ticker.upper()} {self.direction} x{self.multiplier}, sent {self.client_created_at}, input: {self.input_amount} {self.input_ticker.upper()}") 

class CancelMarketAck:
    def __init__(self, data):
        self.success = True if data == None else False
    
    def print(self):
        print(self.success)

