import ex.swap_api as swap
import ex.account_api as account
import logging
import datetime
import win32api
import win32con
import os
import sys
import requests
import math
import time
import threading
from retrying import retry

log_format = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(filename='mylog-rest.json', filemode='a', format=log_format, level=logging.INFO)


def get_timestamp():
    # 获取时间戳
    now = datetime.datetime.now()
    t = now.isoformat("T", "milliseconds")
    return t + 'Z'


def get_timestamp_mini():
    # 获取时间戳
    now = time
    t = now.strftime('%H-%M-%S')
    return t


def message_box():
    # 设置消息提示框内容
    win32api.MessageBox(0, '已平仓!', "提醒", win32con.MB_ICONWARNING)


def trend():
    global maker_l
    global maker_s
    global monitor
    global price_list
    global timer
    global start_time
    global monitor_timer_l
    global monitor_timer_s
    global serial
    global maker
    global tri
    global stop_profit_price
    global average_price

    time_2 = datetime.datetime.now()

    # 设置全局代理
    os.environ['http_proxy'] = 'http://127.0.0.1:1711'
    os.environ['https_proxy'] = 'https://127.0.0.1:1711'
    try:
        requests.get('http://httpbin.org/get')
        # print(response.text)
    except requests.exceptions.ConnectionError as e:
        print('Error', e.args)
        sys.exit(0)

    # 永续合约API
    API_inter = swap.SwapAPI(api_key, secret_key, passphrase, False)
    # 资金账户API
    API_money = account.AccountAPI(api_key, secret_key, passphrase, False)

    while 1:
        time_1 = datetime.datetime.now()
        time_each_circle = abs(time_1 - time_2).microseconds
        time_2 = datetime.datetime.now()
        if monitor == 0:
            time_circle = mini_timer
            start_time = datetime.datetime.now()
        elif float(time_each_circle) >= 1000000 * mini_timer:
            time_circle = 0
        else:
            time_circle = (1000000 * mini_timer - float(time_each_circle)) / 1000000

        # ticker
        ticker = API_inter.get_ticker()  # 公共-获取所有合约的ticker信息
        tickers = {}  # ticker字典初始化
        i = 0
        while i < len(ticker):
            tickers[ticker[i]['instrument_id']] = [ticker[i]['best_ask'], ticker[i]['best_bid'],
                                                   ticker[i]['volume_24h']]
            i += 1

        # 获取价格列表和交易
        while serial < len(instrument_ids):
            best_ask = float(tickers[instrument_ids[serial]][0])  # 卖一价
            best_bid = float(tickers[instrument_ids[serial]][1])  # 买一价
            best_prices[serial] = (best_ask + best_bid) / 2  # 结算标准价列表
            volume = float(tickers[instrument_ids[serial]][2])  # 24h交易量
            position_volume = math.ceil((volume / 1440) / mini_make_position[serial])  # 由成交量决定的下单张数上限（min）
            # excel建仓张数
            position_excel = \
                math.ceil(money * leverages[serial] / best_prices[serial] / BTC_leverage / mini_make_position[serial])
            position[serial] = min(position_volume, position_excel, position_exchanger[serial])  # 建仓张数列表（取以上最小值）

            # 波动监控
            if monitor == 1:
                price_diff_l[serial] = min(price_list[serial]) * (1 + launch_price_ratio[serial])
                price_diff_s[serial] = max(price_list[serial]) * (1 - launch_price_ratio[serial])
                get_off_price_l[serial] = max(price_list[serial]) * (1 - launch_price_ratio[serial]
                                                                     + get_off_modify_ratio[serial])
                get_off_price_s[serial] = min(price_list[serial]) * (1 + launch_price_ratio[serial]
                                                                     - get_off_modify_ratio[serial])
                # 多头建仓
                if (best_prices[serial] >= price_diff_l[serial] >= price_diff_s[serial] and monitor_timer_l[serial] >
                        0 and maker_l[serial] == 0 and maker_s[serial] == 0 and tri[serial] == 1):
                    print('\n', instrument_ids[serial], '开始拉升！')
                    maker_l[serial] = 1  # 多头已建仓
                    maker += 1  # 已有过建仓
                    if serial != BTC_serial:
                        accounts = API_inter.get_coin_account('BTC-USDT-SWAP')  # BTC永续合约账户信息（20次/2s）
                        max_withdraw = accounts['info']['max_withdraw']  # 账户可提现资金string类型
                        API_money.coin_transfer(currency='usdt', amount=max_withdraw, type='0', account_from='9',
                                                account_to='9', instrument_id='btc-usdt',
                                                to_instrument_id=instrument_ids[serial].rstrip('-SWAP').lower())
                        time.sleep(0.05)  # 睡眠保证对方服务器及时更新
                    if tri[serial] == 1:
                        API_inter.take_order(instrument_ids[serial], '1', '', str(position[serial]), client_oid="",
                                             order_type='4', match_price='0')
                        time.sleep(0.05)  # 睡眠保证对方服务器及时更新
                        # positions
                        positions = API_inter.get_specific_position(instrument_ids[serial])  # 单个合约持仓信息 （20次/2s）
                        average_price = float(positions['holding'][0]['avg_cost'])  # 开仓均价
                        stop_profit_price = average_price * (1 + 2 * launch_price_ratio[serial])  # 止盈价格

                # 空头建仓
                elif (best_prices[serial] <= price_diff_s[serial] <= price_diff_l[serial] and monitor_timer_s[serial] >
                      0 and maker_s[serial] == 0 and maker_l[serial] == 0 and tri[serial] == 1):
                    print('\n', instrument_ids[serial], '开始下跌！')
                    maker_s[serial] = 1  # 空头已建仓
                    maker += 1  # 已有过建仓
                    if serial != BTC_serial:
                        accounts = API_inter.get_coin_account('BTC-USDT-SWAP')  # BTC永续合约账户信息（20次/2s）
                        max_withdraw = accounts['info']['max_withdraw']  # 账户可提现资金string类型
                        API_money.coin_transfer(currency='usdt', amount=max_withdraw, type='0', account_from='9',
                                                account_to='9', instrument_id='btc-usdt',
                                                to_instrument_id=instrument_ids[serial].rstrip('-SWAP').lower())
                        time.sleep(0.05)  # 睡眠保证对方服务器及时更新
                    if tri[serial] == 1:
                        API_inter.take_order(instrument_ids[serial], '2', '', str(position[serial]), client_oid="",
                                             order_type='4', match_price='0')
                        time.sleep(0.05)  # 睡眠保证对方服务器及时更新
                        # positions
                        positions = API_inter.get_specific_position(instrument_ids[serial])  # 单个合约持仓信息 （20次/2s）
                        average_price = float(positions['holding'][0]['avg_cost'])  # 开仓均价
                        stop_profit_price = average_price * (1 - 2 * launch_price_ratio[serial])  # 止盈价格
                # 多头平仓
                elif maker_l[serial] == 1 and tri[serial] == 1:
                    # timestamp
                    clock = get_timestamp()
                    equ = open(r'\Trend_record.txt', 'a')  # 记录价格
                    equ.write(instrument_ids[serial])
                    equ.write('---')
                    equ.write(clock)
                    equ.write('---')
                    equ.write(str(round(best_prices[serial], dec[serial])))
                    equ.write('\n')
                    equ.close()
                    if best_prices[serial] <= min(price_list[serial]) or best_prices[serial] <= get_off_price_l[serial]\
                            or best_prices[serial] <= average_price or best_prices[serial] >= stop_profit_price:
                        end_time = datetime.datetime.now()
                        API_inter.take_order(instrument_ids[serial], '3', '', str(position[serial]), client_oid="",
                                             order_type='4', match_price='0')
                        maker_l[serial] = 0  # 多头已平仓
                        equ = open(r'\equity.txt', 'r')
                        equity_init = float(equ.readlines()[-1])
                        equ.close()
                        # 单个币种合约账户信息 （当用户没有持仓时，保证金率为10000）（20次/2s）
                        accounts = API_inter.get_coin_account(instrument_ids[serial])
                        equity_final = float(accounts['info']['equity'])  # 账户权益
                        profit = equity_final - equity_init
                        print('\n', instrument_ids[serial], '平多！利润为：', profit)
                        equ = open(r'\equity.txt', 'a')  # 记录余额
                        equ.write('#######')
                        equ.write(' ')
                        equ.write(clock)
                        equ.write('\n')
                        equ.write(str(equity_final))
                        equ.write('\n')
                        equ.close()
                        equ = open(r'\Trend_record.txt', 'a')
                        equ.write('#######')
                        equ.write('\n')
                        equ.write(str((end_time - start_time).seconds) + 's')
                        equ.write('\n')
                        equ.write('\n')
                        equ.close()
                        monitor = 0
                        # 平仓后将资金转回BTC账户
                        if serial != BTC_serial:
                            accounts = API_inter.get_coin_account(instrument_ids[serial])  # 转入币种永续合约账户信息（20次/2s）
                            max_withdraw = accounts['info']['max_withdraw']  # 账户可提现资金string类型
                            API_money.coin_transfer(currency='usdt', amount=max_withdraw, type='0', account_from='9',
                                                    account_to='9',
                                                    instrument_id=instrument_ids[serial].rstrip('-SWAP').lower(),
                                                    to_instrument_id='btc-usdt')
                        stop_profit_price = 0  # 止盈价格清0
                        average_price = 0  # 开仓均价清0
                        return
                # 空头平仓
                elif maker_s[serial] == 1 and tri[serial] == 1:
                    # timestamp
                    clock = get_timestamp()
                    equ = open(r'\Trend_record.txt', 'a')  # 记录价格
                    equ.write(instrument_ids[serial])
                    equ.write('---')
                    equ.write(clock)
                    equ.write('---')
                    equ.write(str(round(best_prices[serial], dec[serial])))
                    equ.write('\n')
                    equ.close()
                    if best_prices[serial] >= get_off_price_s[serial] or best_prices[serial] >= max(price_list[serial])\
                            or best_prices[serial] >= average_price or best_prices[serial] <= stop_profit_price:
                        end_time = datetime.datetime.now()
                        API_inter.take_order(instrument_ids[serial], '4', '', str(position[serial]), client_oid="",
                                             order_type='4', match_price='0')
                        maker_s[serial] = 0  # 空头已平仓
                        equ = open(r'\equity.txt', 'r')
                        equity_init = float(equ.readlines()[-1])
                        equ.close()
                        # 单个币种合约账户信息 （当用户没有持仓时，保证金率为10000）（20次/2s）
                        accounts = API_inter.get_coin_account(instrument_ids[serial])
                        equity_final = float(accounts['info']['equity'])  # 账户权益
                        profit = equity_final - equity_init
                        print('\n', instrument_ids[serial], '平空！利润为：', profit)
                        equ = open(r'\equity.txt', 'a')  # 记录余额
                        equ.write('#######')
                        equ.write(' ')
                        equ.write(clock)
                        equ.write('\n')
                        equ.write(str(equity_final))
                        equ.write('\n')
                        equ.close()
                        equ = open(r'\Trend_record.txt', 'a')
                        equ.write('#######')
                        equ.write('\n')
                        equ.write(str((end_time - start_time).seconds) + 's')
                        equ.write('\n')
                        equ.write('\n')
                        equ.close()
                        monitor = 0
                        # 平仓后将资金转回BTC账户
                        if serial != BTC_serial:
                            accounts = API_inter.get_coin_account(
                                instrument_ids[serial])  # 转入币种永续合约账户信息 （当用户没有持仓时，保证金率为10000）（20次/2s）
                            max_withdraw = accounts['info']['max_withdraw']  # 账户可提现资金string类型
                            API_money.coin_transfer(currency='usdt', amount=max_withdraw, type='0', account_from='9',
                                                    account_to='9',
                                                    instrument_id=instrument_ids[serial].rstrip('-SWAP').lower(),
                                                    to_instrument_id='btc-usdt')
                        stop_profit_price = 0  # 止盈价格清0
                        average_price = 0  # 开仓均价清0
                        return

            # 先判断，再把价格装入列表
            price_list[serial][timer] = best_prices[serial]

            # 程序初始化时替换0为价格
            if timer == 0:
                for m in range(len(price_list[serial])):
                    if price_list[serial][m] == 0:
                        price_list[serial][m] = best_prices[serial]
            if maker == 0:
                serial += 1  # while循环最末端，没有过建仓时，继续下一币种循环
            else:
                break  # 有过建仓后,币种不再改变，直接跳出币种更新循环，直到程序刷新不再改变本次操作的币种

        # monitor
        clock = get_timestamp_mini()
        end_time = datetime.datetime.now()
        if max(maker_l) == 1:
            print('\r', clock, ' ', '现价:', round(best_prices[serial], dec[serial]), ' ',
                  '止损价:', round(max(get_off_price_l[serial], min(price_list[serial]), average_price), dec[serial]),
                  ' ', '止盈价：', stop_profit_price, '本次运行时长：', (end_time - start_time).seconds, 's', ' ',
                  '上一圈循环时间：', time_each_circle / 1000000, 's', ' ', '本圈循环修正时间：', time_circle, 's', end='')
        elif max(maker_s) == 1:
            print('\r', clock, ' ', '现价:', round(best_prices[serial], dec[serial]), ' ',
                  '止损价:', round(min(get_off_price_s[serial], max(price_list[serial]), average_price), dec[serial]),
                  ' ', '止盈价：', stop_profit_price, '本次运行时长：', (end_time - start_time).seconds, 's', ' ',
                  '上一圈循环时间：', time_each_circle / 1000000, 's', ' ', '本圈循环修正时间：', time_circle, 's', end='')
        else:  # 监控主流币(自选四种）
            print('\r', clock, instrument_ids[0].rstrip('-USDT-SWAP'), '现:', round(best_prices[0], dec[0]),
                  '多:', round(max(price_diff_l[0], price_diff_s[0], dec[0])),
                  '空:', round(min(price_diff_l[0], price_diff_s[0]), dec[0]), '仓:',
                  round(position[0] * mini_make_position[0], 2), ' ',
                  instrument_ids[1].rstrip('-USDT-SWAP'), '现:', round(best_prices[1], dec[1]), '多:',
                  round(max(price_diff_l[1], price_diff_s[1]), dec[1]), '空:',
                  round(min(price_diff_l[1], price_diff_s[1]), dec[1]), '仓:',
                  round(position[1] * mini_make_position[1], 0), ' ', instrument_ids[2].rstrip('-USDT-SWAP'),
                  '现:', round(best_prices[2], dec[2]), '多:',
                  round(max(price_diff_l[2], price_diff_s[2]), dec[2]), '空:',
                  round(min(price_diff_l[2], price_diff_s[2]), dec[2]), '仓:',
                  round(position[2] * mini_make_position[2], 1), ' ', instrument_ids[3].rstrip('-USDT-SWAP'),
                  '现:', round(best_prices[3], dec[3]), '多:',
                  round(max(price_diff_l[3], price_diff_s[3]), dec[3]), '空:',
                  round(min(price_diff_l[3], price_diff_s[3]), dec[3]), '仓:',
                  round(position[3] * mini_make_position[3], 1), ' ', '已跑：',
                  (end_time - start_time).seconds, 's', '上圈：',
                  round(time_each_circle / 1000000, 2), 's', '修正：', round(time_circle, 4), 's', end='')

        monitor = 1  # 启动波动监控
        if maker == 0:
            serial = 0  # 无建仓，从头开始币种循环，有过建仓后，币种不再改变。

        time.sleep(time_circle)
        timer += 1
        if timer >= math.ceil(time_monitor / mini_timer):
            timer = 0


# @retry
def restart():
    global maker_l
    global maker_s
    global monitor
    global price_list
    global timer
    global start_time
    global monitor_timer_l
    global monitor_timer_s
    global serial
    global maker
    global tri
    global stop_profit_price
    global average_price

    try:
        trend()
    except (requests.exceptions.ProxyError, requests.exceptions.RequestException, requests.exceptions.HTTPError,
            requests.exceptions.ConnectionError, requests.exceptions.SSLError, requests.exceptions.Timeout,
            requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.RetryError) as e:
        print('\n', "错误信息：", e)
        restart()
    else:
        print('\n', '已平仓！', '\n')


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

    # 手动设置参数
    get_off_modify_ratio = [-0.0005, -0.0005, -0.0005, -0.0005]  # 顶点后撤修正率，平仓修正率，越大则越易平仓，越小平仓越难，同时也越抗中继震荡（经验）
    time_monitor = 0.5  # 监控的时段长度（s）(根据实际每圈运行时间调整）
    mini_timer = 0.1  # 价格更新间隔（s）
    money = 500  # 下单金额（$）（考虑杠杆后，以BTC为准）（excel）
    BTC_leverage = 100  # 比特币杠杆
    BTC_serial = 0  # BTC对应的i值
    # 操作币种（一般选主流币。交易所，定期更新）
    instrument_ids = ['BTC-USDT-SWAP', 'LTC-USDT-SWAP', 'ETH-USDT-SWAP', 'BCH-USDT-SWAP']
    launch_price_ratio = [0.0015, 0.002, 0.002, 0.002]  # 启动价格变化比例（经验）
    mini_make_position = [0.01, 1, 0.1, 0.1]  # 每张对应货币数or单笔最小下单货币数（交易所，定期更新）
    dec = [1, 2, 2, 2, 2]  # 价格小数位数（交易所，定期更新）
    position_exchanger = [1000, 500, 2000, 1000]  # 交易所最大建仓张数（交易所，定期更新）
    leverages = [100, 50, 50, 50]  # 各币种最大杠杆率

    # 初始化
    best_prices = [0 for _ in range(len(instrument_ids))]  # 结算标准价列表初始化
    position = [0 for _ in range(len(instrument_ids))]  # 建仓张数初始化
    price_diff_l = [0 for _ in range(len(instrument_ids))]  # 做多价格初始化
    price_diff_s = [0 for _ in range(len(instrument_ids))]  # 做空价格初始化
    get_off_price_l = [0 for _ in range(len(instrument_ids))]  # 平多价格初始化
    get_off_price_s = [0 for _ in range(len(instrument_ids))]  # 平空价格初始化

    while 1:

        # 全局变量
        stop_profit_price = 0  # 止盈价格
        average_price = 0  # 开仓均价
        tri = [1 for _ in range(len(instrument_ids))]  # 建仓开关（1开0关）
        maker = 0  # 标记是否有过建仓（1有0无）
        serial = 0  # 币种序号
        monitor_timer_l = [1 for _ in range(len(instrument_ids))]  # 开始多头波动监控计时（1开0关）
        monitor_timer_s = [1 for _ in range(len(instrument_ids))]  # 开始空头波动监控计时（1开0关）
        timer = 0  # 价格记录计时
        maker_l = [0 for _ in range(len(instrument_ids))]  # 多头建仓系数
        maker_s = [0 for _ in range(len(instrument_ids))]  # 空头建仓系数
        monitor = 0  # 初次记录系数
        start_time = 0  # 记录开始时间
        price_list = [0 for _ in range(len(instrument_ids))]  # 价格列表初始化
        lmn = 0
        while lmn < len(instrument_ids):
            price_list[lmn] = [0 for _ in range(math.ceil(time_monitor / mini_timer))]  # 初始化价格列表
            lmn += 1

        restart()
