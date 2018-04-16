# From catalyst examples
import talib
from logbook import Logger

from catalyst.api import order, order_target_percent, record, get_open_orders


NAMESPACE = "buy_low_sell_high"
log = Logger(NAMESPACE)


def initialize(context):
    context.TARGET_POSITIONS = 30
    context.PROFIT_TARGET = 0.1
    context.SLIPPAGE_ALLOWED = 0.02

    context.errors = []


def perform_ta(context, data):
    price = data.current(context.asset, "price")
    log.info("got price {price}".format(price=price))

    prices = data.history(context.asset, fields="price", bar_count=20, frequency="1D")
    rsi = talib.RSI(prices.values, timeperiod=14)[-1]
    log.info("got rsi: {}".format(rsi))

    # Buying more when RSI is low, this should lower our cost basis
    if rsi <= 30:
        buy_increment = 1
    elif rsi <= 40:
        buy_increment = 0.5
    elif rsi <= 70:
        buy_increment = 0.2
    else:
        buy_increment = 0.1

    cash = context.portfolio.cash
    log.info("base currency available: {cash}".format(cash=cash))

    record(price=price, rsi=rsi)

    orders = get_open_orders(context.asset)
    if orders:
        log.info("skipping bar until all open orders execute")
        return

    is_buy = False
    cost_basis = None
    if context.asset in context.portfolio.positions:
        position = context.portfolio.positions[context.asset]

        cost_basis = position.cost_basis
        log.info(
            "found {amount} positions with cost basis {cost_basis}".format(
                amount=position.amount, cost_basis=cost_basis
            )
        )

        if position.amount >= context.TARGET_POSITIONS:
            log.info("reached positions target: {}".format(position.amount))
            return

        if price < cost_basis:
            is_buy = True
        elif (position.amount > 0 and price > cost_basis * (1 + context.PROFIT_TARGET)):
            profit = (price * position.amount) - (cost_basis * position.amount)
            log.info("closing position, taking profit: {}".format(profit))
            order_target_percent(
                asset=context.asset, target=0, limit_price=price * (1 - context.SLIPPAGE_ALLOWED)
            )
        else:
            log.info("no buy or sell opportunity found")
    else:
        is_buy = True

    if is_buy:
        if buy_increment is None:
            log.info("the rsi is too high to consider buying {}".format(rsi))
            return

        if price * buy_increment > cash:
            log.info("not enough base currency to consider buying")
            return

        log.info("buying position cheaper than cost basis {} < {}".format(price, cost_basis))
        order(
            asset=context.asset,
            amount=buy_increment,
            limit_price=price * (1 + context.SLIPPAGE_ALLOWED)
        )


def trade_logic(context, data):
    log.info("handling bar {}".format(data.current_dt))
    # try:
    perform_ta(context, data)
    # except Exception as e:
    #     log.warn('aborting the bar on error {}'.format(e))
    #     context.errors.append(e)

    log.info(
        "completed bar {}, total execution errors {}".format(data.current_dt, len(context.errors))
    )

    if len(context.errors) > 0:
        log.info("the errors:\n{}".format(context.errors))
