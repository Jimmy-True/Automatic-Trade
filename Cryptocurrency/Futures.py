import ex.futures_api as future
import logging
import math
import time
import os
import sys
import requests

log_format = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(filename='okex/mylog-rest.json', filemode='a', format=log_format, level=logging.INFO)


def make_position():

    # 设置全局代理
    os.environ['http_proxy'] = 'http://127.0.0.1:1711'
    os.environ['https_proxy'] = 'https://127.0.0.1:1711'

    # 交割合约API
    futuresAPI = future.FutureAPI(api_key, secret_key, passphrase, False)

    # 手动设定

    # 不要做空！

    direction = 0  # 建空
    direction = 1  # 建多

    total_amount = 1  # 总共下单数字货币数量(excel)
    make_timer = 20  # 分拆单总数（根据交易习惯调整）

    price_make_s_end = 49200  # 建空或者平多终止建仓价格(0)
    price_make_s = 48600  # 建空或者平多起始建仓价格(0)
    price_make_l = 42000  # 建多或者平空起始建仓价格(1)
    price_make_l_end = 39000  # 建多或者平空终止建仓价格(1)

    futrues_switcher = 1  # 切换模式，0金本位1币本位
    # stop_price = 5100  # 止损价格
    coin = 'BTC-USD-210326'  # 交易币种
    dec = 2  # 价格小数位数
    contract_mini = 1  # 最小下单单位数字货币小数位数(金本位使用，例如1对应0.1ETH）
    futures_mini_price = 100  # 最小下单数字货币对应美元(币本位使用）
    counter = 0  # 计数器
    price_ratio = 0  # 价格变化率
    promotion_ratio = 2 / make_timer  # 每笔小单递增系数
    if direction == 0 or direction == 3:
        price_ratio = (price_make_s_end - price_make_s) / (make_timer - 1) / price_make_s  # 开空或平多价格变化率
    elif direction == 1 or direction == 2:
        price_ratio = (price_make_l - price_make_l_end) / (make_timer - 1) / price_make_l  # 开多或平空价格变化率
    # tri = 0  # 止损策略单控制参数
    zhangshu = 0

    # modify ratio
    modify_ratio = make_timer / ((math.pow((1 + promotion_ratio), make_timer) - 1) / promotion_ratio)  # 修正系数，确保建仓总数不超标

    if futrues_switcher == 0:
        coin_amount = round(total_amount / make_timer, contract_mini)  # 每单数字货币数量
        contract_val = math.pow(0.1, contract_mini)  # 最小下单数字货币量
        zhangshu = modify_ratio * coin_amount / contract_val  # 下单张数

    i = 0

    if direction == 0:  # 建空
        if futrues_switcher == 1 and i == 0:
            make_money = price_make_s * total_amount  # 下单总金额
            zhangshu = modify_ratio * (make_money / futures_mini_price) / make_timer
        price_op = round(price_make_s * price_ratio, dec)
        while i < make_timer:
            zhangshu = zhangshu * (1 + promotion_ratio)
            id = futuresAPI.take_order(coin, '2', str(price_make_s),
                                       str(math.ceil(zhangshu)), client_oid="",
                                       order_type='0', match_price='0')['order_id']  # 卖出建空
            print(id)
            counter = counter + math.ceil(zhangshu)
            price_make_s = price_make_s + price_op
            i += 1
        print(counter, '张')

    elif direction == 1:  # 建多
        if futrues_switcher == 1 and i == 0:
            make_money = price_make_l * total_amount  # 下单总金额
            zhangshu = modify_ratio * (make_money / futures_mini_price) / make_timer
        price_op = round(price_make_l * price_ratio, dec)
        while i < make_timer:
            zhangshu = zhangshu * (1 + promotion_ratio)
            id = futuresAPI.take_order(coin, '1', str(price_make_l),
                                       str(math.ceil(zhangshu)), client_oid="",
                                       order_type='0', match_price='0')['order_id']  # 买入建多
            print(id)
            counter = counter + math.ceil(zhangshu)
            price_make_l = price_make_l - price_op
            i += 1
        print(counter, '张')

    elif direction == 2:  # 平空
        if futrues_switcher == 1 and i == 0:
            make_money = price_make_l * total_amount  # 下单总金额
            zhangshu = modify_ratio * (make_money / futures_mini_price) / make_timer
        price_op = round(price_make_l * price_ratio, dec)
        while i < make_timer:
            zhangshu = zhangshu * (1 + promotion_ratio)
            id = futuresAPI.take_order(coin, '4', str(price_make_l),
                                       str(math.ceil(zhangshu)), client_oid="",
                                       order_type='0', match_price='0')['order_id']  # 买入平空
            print(id)
            counter = counter + math.ceil(zhangshu)
            price_make_l = price_make_l - price_op
            i += 1
        print(counter, '张')

    elif direction == 3:  # 平多
        if futrues_switcher == 1 and i == 0:
            make_money = price_make_s * total_amount  # 下单总金额
            zhangshu = modify_ratio * (make_money / futures_mini_price) / make_timer
        price_op = round(price_make_s * price_ratio, dec)
        while i < make_timer:
            zhangshu = zhangshu * (1 + promotion_ratio)
            id = futuresAPI.take_order(coin, '3', str(price_make_s),
                                       str(math.ceil(zhangshu)), client_oid="",
                                       order_type='0', match_price='0')['order_id']  # 卖出平多
            print(id)
            counter = counter + math.ceil(zhangshu)
            price_make_s = price_make_s + price_op
            i += 1
        print(counter, '张')


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

    make_position()

