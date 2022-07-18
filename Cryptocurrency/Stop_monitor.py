import ex.swap_api as swap
import logging
import datetime
import os
import requests
import sys
from retrying import retry
import time

log_format = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(filename='mylog-rest.json', filemode='a', format=log_format, level=logging.INFO)


def get_timestamp():
    now = datetime.datetime.now()
    t = now.isoformat("T", "milliseconds")
    return t + "Z"


def take_stop():

    # 设置全局代理
    os.environ['http_proxy'] = 'http://127.0.0.1:1711'
    os.environ['https_proxy'] = 'https://127.0.0.1:1711'
    try:
        response = requests.get('http://httpbin.org/get')
        # print(response.text)
    except requests.exceptions.ConnectionError as e:
        print('Error', e.args)
        print('retrying......')
        sys.exit(0)

    global tri_l
    global tri_s

    # swap api test
    # 永续合约API
    swapAPI = swap.SwapAPI(api_key, secret_key, passphrase, False)
    # 手动设定
    stop_ratio = 0.0065  # 止损价格百分比，excel
    coin = 'BTC-USDT-SWAP'  # 操作货币类型
    decimal = 1  # 价格小数位数
    mini_make = 0.01  # 最小下单单位
    while 1:
        time.sleep(0.2)
        # positions
        positions = swapAPI.get_specific_position(coin)  # 单个合约持仓信息 （20次/2s）
        profit = round(float(positions['holding'][0]['unrealized_pnl']) +
                       float(positions['holding'][0]['realized_pnl']) +
                       float(positions['holding'][0]['settled_pnl']), 2)
        side = positions['holding'][0]['side']
        if side == 'long':
            position_l = int(positions['holding'][0]['position'])  # 多头持仓量
            position_s = 0  # 空头持仓量
            avg_l = float(positions['holding'][0]['avg_cost'])  # 多头开仓均价
            avg_s = 0  # 空头开仓均价
        elif side == 'short':
            position_s = int(positions['holding'][0]['position'])  # 空头持仓量
            position_l = 0  # 多头持仓量
            avg_s = float(positions['holding'][0]['avg_cost'])  # 空头开仓均价
            avg_l = 0  # 多头开仓均价
        # price
        tickers = swapAPI.get_specific_ticker(coin)
        best_ask = float(tickers['best_ask'])  # 卖一价
        best_bid = float(tickers['best_bid'])  # 买一价
        best_price = (best_ask + best_bid) / 2  # 结算标准价
        # monitor
        clock = get_timestamp()
        if position_l == 0 and position_s == 0:
            profit_ratio = 0
        else:
            profit_ratio = round((100 * profit) / (position_l * mini_make * avg_l + position_s * mini_make * avg_s), 3)
        print('\r', clock, '当前盈利：', profit, ' ', profit_ratio, '%', '现价：', round(best_price, decimal), end='')
        if tri_l == 0 and position_l > 0:
            price_stop = round((1 - stop_ratio) * avg_l, decimal)  # 多头止损价格
            # 多头策略止损
            swapAPI.take_order_algo(coin, '3', '1', position_l, trigger_price=price_stop, algo_type='2')
            tri_l = 1
        elif tri_s == 0 and position_s > 0:
            price_stop = round((1 + stop_ratio) * avg_s, decimal)  # 空头止损价格
            # 空头策略止损
            swapAPI.take_order_algo(coin, '4', '1', position_s, trigger_price=price_stop, algo_type='2')
            tri_s = 1
        elif position_l == 0 and position_s > 0:
            tri_l = 0
        elif position_s == 0 and position_l > 0:
            tri_s = 0
        elif position_l == 0 and position_s == 0:
            tri_l = 0
            tri_s = 0


@retry
def restart():
    global tri_l
    global tri_s
    try:
        take_stop()
    except (requests.exceptions.ProxyError, requests.exceptions.RequestException, requests.exceptions.HTTPError,
            requests.exceptions.ConnectionError, requests.exceptions.SSLError, requests.exceptions.Timeout,
            requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.RetryError) as e:
        print('\n', "错误信息：", e)
        restart()


if __name__ == '__main__':

    # 设置API密码

    # # Watch_Only
    api_key = ""
    secret_key = ""
    passphrase = ""

    # Trade_Allowed
    api_key = ""
    secret_key = ""
    passphrase = ""

    tri_l = 0
    tri_s = 0
    restart()

