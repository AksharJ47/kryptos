import matplotlib.pyplot as plt
import numpy as np
import os
from catalyst.exchange.utils.stats_utils import extract_transactions
from logbook import Logger

from kryptos import logger_group
from kryptos.settings import PERF_DIR

log = Logger("VIZ")
logger_group.add_logger(log)


def show_plot():
    """Prevents crashing when scrolling on macOS"""
    while True:
        try:
            plt.show()
        except UnicodeDecodeError:
            continue

        break


def save_plot(config, name):
    if not isinstance(config, dict):
        config = config.__dict__
    FIG_PATH = os.path.join(PERF_DIR, "figures")
    if not os.path.exists(FIG_PATH):
        os.makedirs(FIG_PATH)
    f_path = os.path.join(FIG_PATH, "{}.png".format(name))
    plt.savefig(f_path, bbox_inches="tight", dpi=300)


def get_start_geo(num_plots, cols=1):
    fig = plt.figure(figsize=(6, 14))
    start = int(str(num_plots) + str(cols) + "1")
    return start


def add_legend():
    # plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    plt.legend(loc="upper center", bbox_to_anchor=(0.5, -0.2), fancybox=True, shadow=True, ncol=5)


def add_twin_legends(axes):
    lines = []
    for ax in axes:
        lines.extend(ax.get_lines())

    plt.legend(lines, [line.get_label() for line in lines])


def plot_portfolio(context, results, name=None, pos=211):
    # Get the base_currency that was passed as a parameter to the simulation
    exchange = list(context.exchanges.values())[0]
    if exchange.base_currency:
        base_currency = exchange.base_currency.upper
    else:
        base_currency = ''

    # First chart: Plot portfolio value using base_currency
    ax = plt.subplot(pos)

    val = results.loc[:, ["portfolio_value"]]
    ax.plot(val, label=name)

    ax.set_ylabel("Portfolio Value\n({})".format(base_currency))
    start, end = ax.get_ylim()
    ax.yaxis.set_ticks(np.arange(start, end, (end - start) / 5))


def plot_percent_return(results, name=None, pos=211):
    if name is None:
        name = "Strategy"
    ax1 = plt.subplot(pos)
    ax1.set_ylabel("Percent Return (%)")
    res = results.loc[:, ["algorithm_period_return"]]
    ax1.plot(res, label=name)


def plot_benchmark(results, pos=211):
    ax = plt.subplot(pos)
    bench = results.loc[:, ["benchmark_period_return"]]
    ax.plot(bench, label="Benchmark", linestyle="--")


def plot_as_points(results, column, pos, y_val=None, label=None, marker="o", color="green"):
    ax = plt.subplot(pos)

    res = results.loc[:, [column]]

    ax.scatter(results.index.to_pydatetime(), res, marker=marker, s=5, c=color, label=label)


def plot_column(results, column, pos, y_label=None, label=None, add_mean=False, twin=None, **kw):
    if y_label is None:
        y_label = "{}".format(column.replace("_", "\n").title())

    if results[column].isnull().all():
        log.error("Not enough data to plot {}".format(column))
        ax = plt.subplot(pos)
        ax.set_ylabel(y_label)
        return ax

    if twin is None:
        ax = plt.subplot(pos)
    else:
        ax = twin.twinx()
    ax.set_ylabel(y_label)

    res = results.loc[:, [column]]
    ax.plot(res, label=label, **kw)

    if add_mean:
        mean = [np.mean(res) for i in res.index]
        ax.plot(res, label=label)
        ax.plot(res.index, mean, linestyle="--", label="mean")

    return ax


def plot_bar(results, column, pos, label=None, twin=None, **kw):
    if twin is None:
        ax = plt.subplot(pos)
    else:
        ax = twin.twinx()

    res = results.loc[:, [column]]
    ax.bar(res.index, res[column].values, label=label, **kw)


def mark_on_line(results, pos, y_val=None, label=None, marker="o", color="green"):
    ax = plt.subplot(pos)
    ax.scatter(
        results.index.to_pydatetime(),
        results.loc[results.index, y_val],
        marker=marker,
        s=50,
        c=color,
        label=label,
    )


def plot_buy_sells(results, pos, y_val=None):
    # Plot the price increase or decrease over time.

    if y_val is None:
        y_val = "price"
        ax = plot_column(results, "price", pos, y_label="Buy/Sells")

    else:  # dont plot price if using other y_val
        ax = plt.subplot(pos)

    transaction_df = extract_transactions(results)
    if not transaction_df.empty:
        buy_df = transaction_df[transaction_df["amount"] > 0]
        sell_df = transaction_df[transaction_df["amount"] < 0]
        ax.scatter(
            buy_df.index.to_pydatetime(),
            results.loc[buy_df.index, y_val],
            marker="^",
            s=100,
            c="green",
            label="",
        )
        ax.scatter(
            sell_df.index.to_pydatetime(),
            results.loc[sell_df.index, y_val],
            marker="v",
            s=100,
            c="red",
            label="",
        )
