from catalyst import run_algorithm
from catalyst.api import record, set_benchmark, symbol, get_open_orders, order, cancel_order, get_dataset
from catalyst.exchange.exchange_errors import PricingDataNotLoadedError

from crypto_platform.utils import load, viz
from crypto_platform.analysis.indicators import TAAnalysis
from crypto_platform.config import CONFIG
from crypto_platform.datasets.google_trends.manager import GoogleTrendDataManager
from logbook import Logger

import click
import matplotlib.pyplot as plt


log = Logger('Blockchain Activity')


@click.command()
@click.argument('keyword')
def run(keyword):

    click.secho('Analysis Google Trends:\n{}'.format(keyword), fg='white')

    trends = GoogleTrendDataManager([keyword])

    def initialize(context):

        context.ORDER_SIZE = 10
        context.SLIPPAGE_ALLOWED = 0.05
        context.BARS = 365

        context.swallow_errors = True
        context.errors = []

        context.ASSET_NAME = CONFIG.ASSET
        context.asset = symbol(context.ASSET_NAME)
        context.market = symbol(CONFIG.ASSET)

        set_benchmark(context.asset)

    def handle_data(context, data):
        date = context.blotter.current_dt.date()

        price = data.current(context.asset, 'price')
        record_payload = {'price': price}

        if date in trends.df.index:
            current_val = trends.kw_by_date(keyword, date)
            record_payload[keyword] = current_val

        record(**record_payload)

    def analyze(context, results):
        viz.plot_metric(results, 'price', pos=211, label='Price')
        viz.plot_metric(results, keyword, pos=212, y_label=keyword, label='Interest over time')
        plt.legend()

    try:
        run_algorithm(
            capital_base=CONFIG.CAPITAL_BASE,
            data_frequency=CONFIG.DATA_FREQUENCY,
            initialize=initialize,
            handle_data=handle_data,
            analyze=analyze,
            exchange_name=CONFIG.BUY_EXCHANGE,
            base_currency=CONFIG.BASE_CURRENCY,
            start=CONFIG.START,
            end=CONFIG.END,
        )
    except PricingDataNotLoadedError:
        log.info('Ingesting required exchange bundle data')
        load.ingest_exchange(CONFIG)

    viz.add_legend()
    viz.show_plot()


if __name__ == '__main__':
    run()