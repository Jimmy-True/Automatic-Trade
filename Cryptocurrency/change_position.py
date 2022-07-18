import ex.swap_api as swap
import logging
import math
import os
import sys
import requests
import time
import win32api
import win32con

log_format = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(filename='mylog-rest.json', filemode='a', format=log_format, level=logging.INFO)


def change_position():

    # 设置全局代理
    os.environ['http_proxy'] = 'http://127.0.0.1:1711'
    os.environ['https_proxy'] = 'https://127.0.0.1:1711'
    try:
        response = requests.get('http://httpbin.org/get')
        # print(response.text)
    except requests.exceptions.ConnectionError as e:
        print('Error', e.args)
        sys.exit(0)

    # 永续合约API
    swapAPI = swap.SwapAPI(api_key, secret_key, passphrase, False)

    # 设定参数
    coin = 'ETH-USDT-SWAP'  # 交易币种
    dec = 2  # 价格小数位数
    coin_amount = 1  # 每单数字货币数量
    contract_val = 0.1  # 最小下单单位
    price_op = 15  # 价格变化系数
    direction = 0  # 选择仓位优化方向（0优化、平空补多 1优化、平多补空 2平空补多 3平多补空）

    mini_price = math.pow(0.1, dec)  # 价格最小变化值
    tickers = swapAPI.get_specific_ticker(coin)
    best_ask = float(tickers['best_ask'])  # 卖一价
    best_bid = float(tickers['best_bid'])  # 买一价

    if direction == 0:  # 优化空头仓位
        swapAPI.take_order(coin, '4', str(best_bid - (price_op * mini_price)),
                           str(int(coin_amount / contract_val)), client_oid="",
                           order_type='0', match_price='0')  # 买入平空
        swapAPI.take_order(coin, '1', str(best_bid - (price_op * mini_price)),
                           str(int(coin_amount / contract_val)), client_oid="",
                           order_type='0', match_price='0')  # 买入补多
        print('已优化空头仓位')

    elif direction == 1:  # 优化多头仓位
        swapAPI.take_order(coin, '3', str(best_ask + (price_op * mini_price)),
                           str(int(coin_amount / contract_val)), client_oid="",
                           order_type='0', match_price='0')  # 卖出平多
        swapAPI.take_order(coin, '2', str(best_ask + (price_op * mini_price)),
                           str(int(coin_amount / contract_val)), client_oid="",
                           order_type='0', match_price='0')  # 卖出补空
        print('已优化多头仓位')

    elif direction == 2:  # 平仓空头仓位
        timer = 0
        while 1:
            tickers = swapAPI.get_specific_ticker(coin)
            best_bid = float(tickers['best_bid'])  # 买一价
            time.sleep(3)
            swapAPI.take_order(coin, '4', str(best_bid - (price_op * mini_price)),
                               str(int(coin_amount / contract_val)), client_oid="",
                               order_type='0', match_price='0')  # 买入平空
            swapAPI.take_order(coin, '1', str(best_bid - (price_op * mini_price)),
                               str(int(coin_amount / contract_val)), client_oid="",
                               order_type='0', match_price='0')  # 买入补多
            timer += 1
            if timer >= 10:
                win32api.MessageBox(0, '已循环十次，如需停止请关闭程序', "提醒", win32con.MB_ICONWARNING)
                timer = 0

    elif direction == 3:  # 平仓多头仓位
        timer = 0
        while 1:
            tickers = swapAPI.get_specific_ticker(coin)
            best_ask = float(tickers['best_ask'])  # 卖一价
            time.sleep(3)
            swapAPI.take_order(coin, '3', str(best_ask + (price_op * mini_price)),
                               str(int(coin_amount / contract_val)), client_oid="",
                               order_type='0', match_price='0')  # 卖出平多
            swapAPI.take_order(coin, '2', str(best_ask + (price_op * mini_price)),
                               str(int(coin_amount / contract_val)), client_oid="",
                               order_type='0', match_price='0')  # 卖出补空
            timer += 1
            if timer >= 10:
                win32api.MessageBox(0, '已循环十次，如需停止请关闭程序', "提醒", win32con.MB_ICONWARNING)
                timer = 0


if __name__ == '__main__':

    # 设置API密码

    # Watch_Only
    api_key = ""
    secret_key = ""
    passphrase = ""

    # Trade_Allowed
    api_key = ""
    secret_key = ""
    passphrase = ""

    change_position()

