import ex.swap_api as swap
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
logging.basicConfig(filename='okex/mylog-rest.json', filemode='a', format=log_format, level=logging.INFO)


def get_timestamp():
    # 获取时间戳
    now = datetime.datetime.now()
    t = now.isoformat("T", "milliseconds")
    return t + "Z"


def message_box(profit):
    # 设置消息提示框内容
    win32api.MessageBox(0, '触发止损，或已平仓。收益为' + str(profit), "提醒", win32con.MB_ICONWARNING)


def swap_my():
    # 设置全局代理
    os.environ['http_proxy'] = 'http://127.0.0.1:1711'
    os.environ['https_proxy'] = 'https://127.0.0.1:1711'
    try:
        requests.get('http://httpbin.org/get')
    except requests.exceptions.ConnectionError as e:
        print('Error', e.args)
        sys.exit(0)

    # 设置全局变量
    global lever
    global maker
    global taker_timer
    global hang
    global swap_ratio
    global swap_ratio_estimated
    global coin

    # 激活以强制启动某些功能
    # maker = 1  # 关闭挂单功能
    # lever = 1  # 关闭杠杆调整功能
    # taker_timer = 200  # 挂单已有成交，启用止损监控
    # hang = 1  # 已挂平仓单

    # 某些功能开关（0开1关）
    close_tri = 0  # 平仓动作开关

    # 永续合约API
    API_inter = swap.SwapAPI(api_key, secret_key, passphrase, False)

    # 手动设置参数
    maker_modify_ratio = 2  # 挂单时价格修正，确保maker
    mini_price = 0.1  # 最小价格变化（交易所）
    unit_batch_cancel_amount = 10  # 单次批量撤单单数（交易所）
    total_amount = 975  # 总下单张数(excel)
    max_amount = 400  # 策略单最大单笔下单张数（交易所）
    leverage = 100  # 杠杆（数值越大收益越高，excel）
    dec = 1  # 价格小数位数（交易所）
    modify_ratio_list = [0.0021, 0.005]  # 平仓价格系数（excel)
    unit_price_ratio = 0.001  # 每个挂单之间价格间隔ratio(excel)
    stop_ratio = 0.135  # 止损价格百分比（excel）
    # 阶梯挂单数量设置（excel）
    position_amount = [10, 15, 20, 25, 30, 30]
    # 单位挂单张数设置（excel）
    unit_amount = [1, 1, 2, 4, 8, 19]

    # 初始化参数
    # 调整switch参数，也要考虑大趋势！
    swap_ratio = float(swap_ratio)
    swap_ratio_estimated = float(swap_ratio_estimated)
    # 强势看涨
    if 0 < swap_ratio <= swap_ratio_estimated:
        switch = 1
    # 强势看跌
    elif 0 > swap_ratio >= swap_ratio_estimated:
        switch = 0
    # 震荡空转多
    elif swap_ratio <= 0 and swap_ratio_estimated >= 0:
        switch = 1
    # 其他情况根据目前位置调整，主要方向
    else:
        switch = 0

    # 手动激活以强制启动某些功能
    # switch =  #   # 切换多空（0空1多）

    print('switch:', switch)

    position_total = 0
    # 对列表元素求和
    for m in position_amount:
        if type(m) is list:
            for n in m:
                if type(n) is int:
                    position_total += n
        elif type(m) is int:
            position_total += m
    position_l = 0
    position_s = 0
    avg_l = 0
    avg_s = 0
    if lever == 0:
        API_inter.set_leverage(coin, leverage, 3)  # 设定某个合约的杠杆 （5次/2s）
    lever = 1
    list_length = len(position_amount)  # 列表元素个数

    while 1:
        time.sleep(0.05)
        # timestamp
        clock = get_timestamp()
        # positions
        positions = API_inter.get_specific_position(coin)  # 单个合约持仓信息 （20次/2s）
        if switch == 0:
            position_l = 0
            position_s = int(positions['holding'][0]['position'])  # 空头持仓量
            avg_l = 0
            avg_s = float(positions['holding'][0]['avg_cost'])  # 空头开仓均价
        elif switch == 1:
            position_l = int(positions['holding'][0]['position'])  # 多头持仓量
            position_s = 0
            avg_l = float(positions['holding'][0]['avg_cost'])  # 多头开仓均价
            avg_s = 0
        # ticker
        tickers = API_inter.get_specific_ticker(coin)  # 公共-获取某个ticker信息 （20次/2s）
        best_ask = float(tickers['best_ask'])  # 卖一价
        best_bid = float(tickers['best_bid'])  # 买一价
        best_price = (best_ask + best_bid) / 2  # 结算标准价

        # 挂单，仅初运行时执行一次
        if maker == 0:
            accounts = API_inter.get_coin_account(coin)  # 单个币种合约账户信息 （当用户没有持仓时，保证金率为10000）（20次/2s）
            equity_init = float(accounts['info']['equity'])  # 初始账户权益
            equ = open(r'/equity_init.txt', 'w')  # 记录初始余额
            equ.write(str(equity_init))
            equ.write('\n')
            equ.close()
            # 初始开单价格
            price_make = round(best_price, dec)
            # 各单价格间隔
            unit_price = round(best_price * unit_price_ratio, dec)

            # 空头挂单
            if switch == 0:
                price_make = price_make + maker_modify_ratio * mini_price  # 修正确保maker
                # 止损价格
                stop_price = round(price_make * (1 + stop_ratio), dec)
                if maker == 0:
                    i = 0
                    while i < list_length:
                        j = 0
                        while j < position_amount[i]:
                            ids = API_inter.take_order(coin, '2', str(price_make), str(unit_amount[i]), client_oid="",
                                                       order_type='', match_price='0')['order_id']  # 空头挂单
                            # 记录日志
                            idr = open(r'/ids.txt', 'a')
                            idr.write(str(ids))
                            idr.write('\n')
                            idr.close()
                            price_make += unit_price
                            j += 1
                            time.sleep(0.05)
                        i += 1
                    # 空头策略止损
                    tri = 1  # 止损策略单控制参数
                    algo_amount = 0  # 止损单数量初始化
                    total_make = total_amount
                    while tri:
                        if total_make > max_amount:
                            total_make -= max_amount
                            algo_amount += 1
                        else:
                            tri = 0
                    while algo_amount >= 0:
                        algo_id = API_inter.take_order_algo(coin, '4', '1', str(total_make), trigger_price=stop_price,
                                                            algo_type='2')['data']["algo_id"]
                        algo_amount -= 1
                        total_make = max_amount
                        # 记录日志
                        algo = open(r'algo_id.txt', 'a')
                        algo.write(str(algo_id))
                        algo.write('\n')
                        algo.close()
                    print('空头挂单完成！将监控成交情况。')
                while 1:
                    time.sleep(0.05)
                    # positions
                    positions = API_inter.get_specific_position(coin)  # 单个合约持仓信息 （20次/2s）
                    position_s = int(positions['holding'][0]['position'])  # 空头持仓量
                    # 检验吃单是否成功
                    if position_s > 0:
                        maker = 1  # 防止重复挂单
                        print('已产生第一笔成交！')
                        break
                    elif taker_timer > 200:
                        print('未能成交，将撤单！')

                        # 撤策略单
                        tri = 1  # 止损策略单控制参数
                        algo_amount = 0  # 止损单数量初始化
                        total_make = total_amount
                        while tri:
                            if total_make > max_amount:
                                total_make -= max_amount
                                algo_amount += 1
                            else:
                                tri = 0
                        algor = open(r'algo_id.txt', 'r')
                        algo_record = algor.readlines()
                        algor.close()
                        i = 0
                        while i <= algo_amount:
                            algo_id = str(algo_record[i]).replace('\n', '').replace('\r', '')  # 策略单id
                            # 撤掉策略单
                            API_inter.cancel_algos(coin, [algo_id], '1')
                            i += 1

                        # 撤限价单
                        batch_cancel_amount = math.ceil(position_total / unit_batch_cancel_amount)  # 批量撤单次数
                        i = 0
                        idr = open(r'/ids.txt', 'r')
                        idr_record = idr.readlines()
                        idr.close()
                        # 开始撤单
                        while i < batch_cancel_amount:
                            j = 0
                            id_list = []
                            # 确定id_list内元素个数
                            num_id_list = position_total - unit_batch_cancel_amount * i
                            if num_id_list > 10:
                                num_id_list = 10
                            else:
                                num_id_list = num_id_list
                            # 将数据导入列表
                            while j < num_id_list:
                                id_list.append(
                                    str(idr_record[j + i *
                                                   unit_batch_cancel_amount]).replace('\n', '').replace('\r', ''))
                                j += 1
                            API_inter.revoke_orders(coin, ids=id_list)
                            time.sleep(0.5)
                            i += 1

                        algo = open(r'algo_id.txt', 'w')  # 清空记录
                        algo.write('')
                        algo.close()
                        idr = open(r'/ids.txt', 'w')  # 清空记录
                        idr.write('')
                        idr.close()
                        taker_timer = 0
                        break
                    else:
                        taker_timer += 1
                        # monitor
                        print('\r', clock, '', '已挂单', round(0.05 * taker_timer, 2), '秒', end='')

            # 多头挂单
            elif switch == 1:
                price_make = price_make - maker_modify_ratio * mini_price  # 修正确保maker
                # 止损价格
                stop_price = round(price_make * (1 - stop_ratio), dec)
                if maker == 0:
                    i = 0
                    while i < list_length:
                        j = 0
                        while j < position_amount[i]:
                            ids = API_inter.take_order(coin, '1', str(price_make), str(unit_amount[i]), client_oid="",
                                                       order_type='', match_price='0')['order_id']  # 多头挂单
                            # 记录日志
                            idr = open(r'/ids.txt', 'a')
                            idr.write(str(ids))
                            idr.write('\n')
                            idr.close()
                            price_make -= unit_price
                            j += 1
                            time.sleep(0.05)
                        i += 1
                    # 多头策略止损
                    tri = 1  # 止损策略单控制参数
                    algo_amount = 0  # 止损单数量初始化
                    total_make = total_amount
                    while tri:
                        if total_make > max_amount:
                            total_make -= max_amount
                            algo_amount += 1
                        else:
                            tri = 0
                    while algo_amount >= 0:
                        algo_id = API_inter.take_order_algo(coin, '3', '1', str(total_make), trigger_price=stop_price,
                                                            algo_type='2')['data']["algo_id"]
                        algo_amount -= 1
                        total_make = max_amount
                        # 记录日志
                        algo = open(r'algo_id.txt', 'a')
                        algo.write(str(algo_id))
                        algo.write('\n')
                        algo.close()
                    print('多头挂单完成！将监控成交情况。')
                while 1:
                    time.sleep(0.05)
                    # positions
                    positions = API_inter.get_specific_position(coin)  # 单个合约持仓信息 （20次/2s）
                    position_l = int(positions['holding'][0]['position'])  # 多头持仓量
                    # 检验吃单是否成功
                    if position_l > 0:
                        maker = 1  # 防止重复挂单
                        print('已产生第一笔成交！')
                        break
                    elif taker_timer > 200:
                        print('未能成交，将撤单！')

                        # 撤策略单
                        tri = 1  # 止损策略单控制参数
                        algo_amount = 0  # 止损单数量初始化
                        total_make = total_amount
                        while tri:
                            if total_make > max_amount:
                                total_make -= max_amount
                                algo_amount += 1
                            else:
                                tri = 0
                        algor = open(r'algo_id.txt', 'r')
                        algo_record = algor.readlines()
                        algor.close()
                        i = 0
                        while i <= algo_amount:
                            algo_id = str(algo_record[i]).replace('\n', '').replace('\r', '')  # 策略单id
                            # 撤掉策略单
                            API_inter.cancel_algos(coin, [algo_id], '1')
                            i += 1

                        # 撤限价单
                        batch_cancel_amount = math.ceil(position_total / unit_batch_cancel_amount)  # 批量撤单次数
                        i = 0
                        idr = open(r'/ids.txt', 'r')
                        idr_record = idr.readlines()
                        idr.close()
                        # 开始撤单
                        while i < batch_cancel_amount:
                            j = 0
                            id_list = []
                            # 确定id_list内元素个数
                            num_id_list = position_total - unit_batch_cancel_amount * i
                            if num_id_list > 10:
                                num_id_list = 10
                            else:
                                num_id_list = num_id_list
                            # 将数据导入列表
                            while j < num_id_list:
                                id_list.append(
                                    str(idr_record[j + i *
                                                   unit_batch_cancel_amount]).replace('\n', '').replace('\r', ''))
                                j += 1
                            API_inter.revoke_orders(coin, ids=id_list)
                            time.sleep(0.5)
                            i += 1

                        algo = open(r'algo_id.txt', 'w')  # 清空记录
                        algo.write('')
                        algo.close()
                        idr = open(r'/ids.txt', 'w')  # 清空记录
                        idr.write('')
                        idr.close()
                        taker_timer = 0
                        break
                    else:
                        taker_timer += 1
                        # monitor
                        print('\r', clock, '', '已挂单', round(0.05 * taker_timer, 2), '秒', end='')

        # 已触发止损，或已平仓，本轮运行结束
        elif position_l == 0 and position_s == 0 and maker == 1:

            # 撤策略单
            tri = 1  # 止损策略单控制参数
            algo_amount = 0  # 止损单数量初始化
            total_make = total_amount
            while tri:
                if total_make > max_amount:
                    total_make -= max_amount
                    algo_amount += 1
                else:
                    tri = 0
            algor = open(r'algo_id.txt', 'r')
            algo_record = algor.readlines()
            algor.close()
            i = 0
            while i <= algo_amount:
                algo_id = str(algo_record[i]).replace('\n', '').replace('\r', '')  # 策略单id
                # 撤掉策略单
                API_inter.cancel_algos(coin, [algo_id], '1')
                i += 1

            # 撤限价单
            batch_cancel_amount = math.ceil(position_total / unit_batch_cancel_amount)  # 批量撤单次数
            i = 0
            idr = open(r'/ids.txt', 'r')
            idr_record = idr.readlines()
            idr.close()
            # 开始撤单
            while i < batch_cancel_amount:
                j = 0
                id_list = []
                # 确定id_list内元素个数
                num_id_list = position_total - unit_batch_cancel_amount * i
                if num_id_list > 10:
                    num_id_list = 10
                else:
                    num_id_list = num_id_list
                # 将数据导入列表
                while j < num_id_list:
                    id_list.append(
                        str(idr_record[j + i * unit_batch_cancel_amount]).replace('\n', '').replace('\r', ''))
                    j += 1
                API_inter.revoke_orders(coin, ids=id_list)
                time.sleep(0.5)
                i += 1

            accounts = API_inter.get_coin_account(coin)  # 单个币种合约账户信息 （当用户没有持仓时，保证金率为10000）（20次/2s）
            equity_final = float(accounts['info']['equity'])  # 账户权益
            equity_init_record = open(r'/equity_init.txt',
                                      'r')
            equity_init = float(equity_init_record.readlines()[0])
            equity_init_record.close()
            profit = equity_final - equity_init  # 净利润
            equ = open(r'/equity.txt', 'a')  # 记录余额
            equ.write('#######')
            equ.write('\n')
            equ.write(clock)
            equ.write('\n')
            equ.write(str(equity_final))
            equ.write('\n')
            equ.close()
            record = open(r'/equity_init.txt', 'w')  # 清空记录
            record.write('')
            record.close()
            algo = open(r'algo_id.txt', 'w')  # 清空记录
            algo.write('')
            algo.close()
            idr = open(r'/ids.txt', 'w')  # 清空记录
            idr.write('')
            idr.close()
            idr = open(r'/close_position.txt', 'w')  # 清空记录
            idr.write('')
            idr.close()

            # 判断是否是止损
            if profit < -100:
                os._exit(0)

            print('\n', '触发止损，或已平仓，本轮运行结束！')
            son_thread = threading.Thread(target=message_box(round(profit, 2)))
            son_thread.start()
            return

        # 监控及挂平仓单
        else:
            # 价格回落触发空头全平挂单
            if switch == 0:
                modify_ratio = (modify_ratio_list[1] - modify_ratio_list[0]) * position_s / total_amount + \
                               modify_ratio_list[0]
                close_price = avg_s * (1 - modify_ratio)
                # monitor
                print('\r', clock, '当前价格：', round(best_price, dec), '空头开仓均价：', avg_s, '平仓价：',
                      round(close_price, dec), '空头仓位：', position_s, 'ratio:', round(modify_ratio, 5), end='')
                # 如果已挂平仓单，则监控是否仓位有变化
                if hang == 1:
                    cp = open(r'/close_position.txt', 'r')
                    cp_id = str(cp.readlines()[0]).replace('\n', '').replace('\r', '')
                    avg_o = round(float(cp.readlines()[1]), dec)
                    cp.close()
                    if avg_o < avg_s:
                        # 撤平仓单
                        API_inter.revoke_order(coin, cp_id)
                        hang = 0
                # 未挂平仓单，则挂单
                elif best_price <= close_price and close_tri == 0 and hang == 0:
                    close_price_real = best_price - maker_modify_ratio * mini_price  # 实际平仓挂单价格
                    cp_id = API_inter.take_order(coin, '4', str(close_price_real), str(position_s), client_oid="",
                                                 order_type='', match_price='0')['data']["algo_id"]  # 挂空头平仓单
                    hang = 1  # 已挂单
                    cp = open(r'/close_position.txt', 'w')  # 记录id
                    cp.write(str(cp_id))
                    cp.write('\n')
                    cp.write(str(avg_s))
                    cp.write('\n')
                    cp.close()
                    time.sleep(1)  # 等待成交

            # 价格回升触发多头全平挂单
            if switch == 1:
                modify_ratio = (modify_ratio_list[1] - modify_ratio_list[0]) * position_l / total_amount + \
                               modify_ratio_list[0]
                close_price = avg_l * (1 + modify_ratio)
                # monitor
                print('\r', clock, '当前价格：', round(best_price, dec), '多头开仓均价：', avg_l, '平仓价：',
                      round(close_price, dec), '多头仓位：', position_l, 'ratio:', round(modify_ratio, 5), end='')
                # 如果已挂平仓单，则监控是否仓位有变化
                if hang == 1:
                    cp = open(r'/close_position.txt', 'r')
                    cp_id = str(cp.readlines()[0]).replace('\n', '').replace('\r', '')
                    avg_o = round(float(cp.readlines()[1]), dec)
                    cp.close()
                    if avg_o > avg_l:
                        # 撤平仓单
                        API_inter.revoke_order(coin, cp_id)
                        hang = 0
                # 未挂平仓单，则挂单
                elif best_price >= close_price and close_tri == 0 and hang == 0:
                    close_price_real = best_price + maker_modify_ratio * mini_price  # 实际平仓挂单价格
                    cp_id = API_inter.take_order(coin, '3', str(close_price_real), str(position_l), client_oid="",
                                                 order_type='', match_price='0')['data']["algo_id"]  # 挂多头平仓单
                    hang = 1  # 已挂单
                    cp = open(r'/close_position.txt', 'w')  # 记录id
                    cp.write(str(cp_id))
                    cp.write('\n')
                    cp.write(str(avg_l))
                    cp.write('\n')
                    cp.close()
                    time.sleep(1)  # 等待成交


@retry
def restart():
    global lever
    global maker
    global taker_timer
    global hang
    global swap_ratio
    global swap_ratio_estimated
    global coin

    try:
        swap_my()
    except (requests.exceptions.ProxyError, requests.exceptions.RequestException, requests.exceptions.HTTPError,
            requests.exceptions.ConnectionError, requests.exceptions.SSLError, requests.exceptions.Timeout,
            requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.RetryError) as e:
        print('\n', "错误信息：", e)
        restart()
    else:
        print('\n', '已平仓！')
        time.sleep(10)  # 时延留下平仓后操作空间


if __name__ == '__main__':
    # 设置API密码

    # # Watch_Only
    api_key = ""
    secret_key = ""
    passphrase = ""

    # # Trade_Allowed
    api_key = ""
    secret_key = ""
    passphrase = ""

    while 1:
        coin = 'BTC-USDT-SWAP'  # 交易币种
        lever = 0  # 修改杠杆记录
        maker = 0  # 挂单成交记录
        taker_timer = 0  # 吃单计时
        hang = 0  # 平仓单挂单记录

        # 永续合约API
        swapAPI = swap.SwapAPI(api_key, secret_key, passphrase, False)
        # 公共-获取合约资金费率 （20次/2s）
        funding_ratio = swapAPI.get_funding_time(coin)
        swap_ratio = funding_ratio['funding_rate']
        swap_ratio_estimated = funding_ratio['estimated_rate']
        restart()
