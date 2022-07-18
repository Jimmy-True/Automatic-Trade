import ex.swap_api as swap
import logging
import datetime
import win32api
import win32con
import os
import sys
import requests
import time
import threading
from retrying import retry


log_format = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(filename='mylog-rest.json', filemode='a', format=log_format, level=logging.INFO)


def get_timestamp():
    # 获取时间戳
    now = datetime.datetime.now()
    t = now.isoformat("T", "milliseconds")
    return t + "Z"


def message_box():
    # 设置消息提示框内容
    win32api.MessageBox(0, '已平仓，10秒后将继续建仓，如需停止请关闭进程', "提醒", win32con.MB_ICONWARNING)


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
    global anomaly_const
    global anomaly_add

    # 手动激活以强制启动某些功能
    # anomaly_const = 1  # 启动恢复模块
    # anomaly_add = 1  # 手动启用。异常恢复时如果已发生加仓行为则启用此选项

    # 某些功能开关（0开1关）
    add_tri = 0  # 加仓动作开关
    close_tri = 0  # 平仓动作开关

    print('anomaly_const:', anomaly_const, '\n', 'anomaly_add:', anomaly_add)

    # 永续合约API
    swapAPI = swap.SwapAPI(api_key, secret_key, passphrase, False)

    # 手动设置参数
    safe_ratio = 0.30  # 预计无回调涨跌幅度（根据市场经验，不低于27%，否则风险太大,excel）
    leverage = 50  # 杠杆（数值越大收益越高，excel）
    init_amount = 1  # 设置初始建仓张数(excel)
    dec = 2  # 价格小数位数
    modify_ratio = 0.003  # 平仓价格系数（excel)
    coin = 'ETH-USDT-SWAP'  # 交易币种
    # 盈利目的头寸基准阶梯加仓张数设置（excel）
    position_p_stage = [14, 18, 36, 81, 194, 475, 1180]
    # 多头补仓价格设置（excel），必须填写止损
    p_l_stage = [0.004, 0.0147, 0.0238, 0.035, 0.049, 0.0665, 0.0882, 0.1]
    # 空头补仓价格设置（excel），必须填写止损
    p_s_stage = [0.004, 0.0147, 0.0238, 0.035, 0.049, 0.0665, 0.0882, 0.1]

    # 初始化参数
    # mini_price = math.pow(0.1, dec)  # 价格最小变化值
    add_l = 0  # 多头补仓计数初始化
    add_s = 0  # 空头补仓计数初始化
    key_prices = []  # 触发价格初始化
    close_price = 0  # 平仓价格初始化
    close_ratio = 0  # 可平仓起点
    # cycle = 0  # 循环因子
    add_p_position = []  # 盈利头寸加仓张数初始化
    algo_id_1 = ''  # 策略单id初始化
    algo_id_2 = ''  # 策略单id初始化
    algo_id = ''  # 策略单id初始化
    if lever == 0:
        swapAPI.set_leverage(coin, leverage, 3)  # 设定某个合约的杠杆 （5次/2s）
    lever = 1
    list_length = len(position_p_stage)  # 列表元素个数减一
    print('列表长度为：', list_length, '即将进入循环！')
    error = 1
    error_1 = 1
    error_2 = 1
    error_3 = 1
    error_4 = 1
    error_5 = 1
    error_6 = 1
    error_7 = 1
    error_8 = 1

    while 1:
        if error == 1:
            print('error!')
            error = 0
        time.sleep(0.05)
        # timestamp
        clock = get_timestamp()
        # positions
        positions = swapAPI.get_specific_position(coin)  # 单个合约持仓信息 （20次/2s）
        position_l = int(positions['holding'][0]['position'])  # 多头持仓量
        position_s = int(positions['holding'][1]['position'])  # 空头持仓量
        avg_l = float(positions['holding'][0]['avg_cost'])  # 多头开仓均价
        avg_s = float(positions['holding'][1]['avg_cost'])  # 空头开仓均价
        # ticker
        tickers = swapAPI.get_specific_ticker(coin)  # 公共-获取某个ticker信息 （20次/2s）
        best_ask = float(tickers['best_ask'])  # 卖一价
        best_bid = float(tickers['best_bid'])  # 买一价
        best_price = (best_ask + best_bid) / 2  # 结算标准价

        # 建仓，仅初运行时执行一次
        if position_l == 0 and position_s == 0 and anomaly_const == 0 and add_l == 0 and add_s == 0:
            if error_1 == 1:
                print('error_1!')
                error_1 = 0
            # 建立仓位
            swapAPI.take_order(coin, '1', '', str(init_amount), client_oid="", order_type='4',
                               match_price='0')  # 多头建仓
            swapAPI.take_order(coin, '2', '', str(init_amount), client_oid="", order_type='4',
                               match_price='0')  # 空头建仓
            time.sleep(0.5)  # 时延确保对方服务器数据及时更新
            positions = swapAPI.get_specific_position(coin)  # 单个合约持仓信息 （20次/2s）
            init_avg_l = float(positions['holding'][0]['avg_cost'])  # 多头初始开仓均价
            init_avg_s = float(positions['holding'][1]['avg_cost'])  # 空头初始开仓均价

            # 盈利头寸加仓张数
            add_p_position = [position_p_stage[0] * init_amount, position_p_stage[1] * init_amount,
                              position_p_stage[2] * init_amount, position_p_stage[3] * init_amount,
                              position_p_stage[4] * init_amount, position_p_stage[5] * init_amount,
                              position_p_stage[6] * init_amount
                              ]
            # 触发补仓价格
            key_prices = [[round((1-p_l_stage[0]) * init_avg_l, dec), round((1+p_s_stage[0]) * init_avg_s, dec)],
                          [round((1-p_l_stage[1]) * init_avg_l, dec), round((1+p_s_stage[1]) * init_avg_s, dec)],
                          [round((1-p_l_stage[2]) * init_avg_l, dec), round((1+p_s_stage[2]) * init_avg_s, dec)],
                          [round((1-p_l_stage[3]) * init_avg_l, dec), round((1+p_s_stage[3]) * init_avg_s, dec)],
                          [round((1-p_l_stage[4]) * init_avg_l, dec), round((1+p_s_stage[4]) * init_avg_s, dec)],
                          [round((1-p_l_stage[5]) * init_avg_l, dec), round((1+p_s_stage[5]) * init_avg_s, dec)],
                          [round((1-p_l_stage[6]) * init_avg_l, dec), round((1+p_s_stage[6]) * init_avg_s, dec)],
                          [round((1-p_l_stage[7]) * init_avg_l, dec), round((1+p_s_stage[7]) * init_avg_s, dec)],
                          [round((1-safe_ratio) * init_avg_l, dec), round((1+safe_ratio) * init_avg_s, dec)]]
            print('初始建仓完成！', '\n', '补仓价格列表：', key_prices)
            # 记录日志
            record = open('My Record.txt', 'w')
            record.write('#######')
            record.write('\n')
            record.write(clock)
            record.write('\n')
            record.write(str(init_avg_s))
            record.write('\n')
            record.write(str(init_avg_l))
            record.write('\n')
            record.write(str(init_amount))
            record.write('\n')
            record.close()

        # 恢复模块。异常发生后,恢复交易信息
        elif anomaly_const == 1:
            if error_2 == 1:
                print('error_2!')
                error_2 = 0
            record = open('My Record.txt', 'r')
            init_record = record.readlines()
            init_amount = float(init_record[-1])  # 初始建仓张数
            init_avg_l = float(init_record[-2])  # 多头初始开仓均价
            init_avg_s = float(init_record[-3])  # 空头初始开仓均价

            # 盈利头寸加仓张数
            add_p_position = [position_p_stage[0] * init_amount, position_p_stage[1] * init_amount,
                              position_p_stage[2] * init_amount, position_p_stage[3] * init_amount,
                              position_p_stage[4] * init_amount, position_p_stage[5] * init_amount,
                              position_p_stage[6] * init_amount]
            # 触发补仓价格
            key_prices = [[round((1-p_l_stage[0]) * init_avg_l, dec), round((1+p_s_stage[0]) * init_avg_s, dec)],
                          [round((1-p_l_stage[1]) * init_avg_l, dec), round((1+p_s_stage[1]) * init_avg_s, dec)],
                          [round((1-p_l_stage[2]) * init_avg_l, dec), round((1+p_s_stage[2]) * init_avg_s, dec)],
                          [round((1-p_l_stage[3]) * init_avg_l, dec), round((1+p_s_stage[3]) * init_avg_s, dec)],
                          [round((1-p_l_stage[4]) * init_avg_l, dec), round((1+p_s_stage[4]) * init_avg_s, dec)],
                          [round((1-p_l_stage[5]) * init_avg_l, dec), round((1+p_s_stage[5]) * init_avg_s, dec)],
                          [round((1-p_l_stage[6]) * init_avg_l, dec), round((1+p_s_stage[6]) * init_avg_s, dec)],
                          [round((1-p_l_stage[7]) * init_avg_l, dec), round((1+p_s_stage[7]) * init_avg_s, dec)],
                          [round((1-safe_ratio) * init_avg_l, dec), round((1+safe_ratio) * init_avg_s, dec)]]
            print('补仓价格列表：', key_prices)
            record.close()
            if anomaly_add == 1:
                add = open('add.txt', 'r')
                init_add = add.readlines()
                close_price = float(init_add[-3])
                add_l = int(float(init_add[-2]))
                add_s = int(float(init_add[-1]))
                print('平仓价格：', close_price, ' ', '完成多头补仓', int(add_l), '次', ' ', '完成空头补仓', int(add_s), '次')
                add.close()
                algo = open('algo_id.txt', 'r')
                init_algo_id = algo.readlines()
                algo_id_1 = str(init_algo_id[-3]).replace('\n', '').replace('\r', '')
                algo_id_2 = str(init_algo_id[-2]).replace('\n', '').replace('\r', '')
                algo_id = str(init_algo_id[-1]).replace('\n', '').replace('\r', '')
                print('策略单id_1：', algo_id_1, ' ', '策略单id_2：', algo_id_2, ' ', '策略单id_3：', algo_id)
                algo.close()
            anomaly_const = 0  # 异常恢复完成
            print(clock, '程序已从异常中恢复！')

        # 已触发止损，或已手动平仓，程序退出
        elif position_l == 0 and position_s == 0:
            if error_3 == 1:
                print('error_3!')
                error_3 = 0
            # 警告
            win32api.MessageBox(0, "触发止损，或已手动平仓，程序将退出！", "提醒", win32con.MB_ICONWARNING)
            record = open('My Record.txt', 'w')
            record.write('')
            record.close()
            add = open('add.txt', 'w')
            add.write('')
            add.close()
            algo = open('algo_id.txt', 'w')
            algo.write('')
            algo.close()
            os._exit(0)

        # 阶梯仓位设置不合理，程序退出
        elif key_prices[-1][0] >= key_prices[-2][0] or key_prices[-1][1] <= key_prices[-2][1]:
            if error_4 == 1:
                print('error_4!')
                error_4 = 0
            # 警告
            win32api.MessageBox(0, "阶梯仓位设置不合理，程序已退出！", "提醒", win32con.MB_ICONWARNING)
            os._exit(0)

        # 补仓及平仓
        else:
            # monitor
            print('\r', clock, '当前价格：', round(best_price, dec), '多头开仓均价：', avg_l, '空头开仓均价：',
                  avg_s, '多头仓位：', position_l, '空头仓位：', position_s, end='')
            add_price_l = key_prices[int(add_l)][0]  # 触发补多价格
            add_price_s = key_prices[int(add_s)][1]  # 触发补空价格

            # 下跌触发多头补仓
            if best_price <= add_price_l and add_tri == 0:
                if error_5 == 1:
                    print('error_5!')
                    error_5 = 0
                # add_l_price = best_bid - (5 * mini_price)  # 补多价格为买一价减去修正
                amount_l = add_p_position[int(add_l)]  # 补多张数
                # position_original = position_l  # 记录现有仓位
                swapAPI.take_order(coin, '1', '', str(amount_l), client_oid="", order_type='4',
                                   match_price='0')  # 多头补多
                time.sleep(0.3)  # 时延确保对方服务器数据及时更新
                positions = swapAPI.get_specific_position(coin)  # 单个合约持仓信息 （20次/2s）
                avg_l = float(positions['holding'][0]['avg_cost'])  # 多头开仓均价
                close_price = avg_l * (1 + modify_ratio * (1 - (add_l / 100)))  # 平仓价

                # 设定止损单
                if add_l == 0:
                    algo_id_1 = swapAPI.take_order_algo(coin, '3', '1', '1500',
                                                        trigger_price=key_prices[list_length][0],
                                                        algo_type='2')['data']["algo_id"]
                    algo_id_2 = swapAPI.take_order_algo(coin, '3', '1', '499', trigger_price=key_prices[list_length][0],
                                                        algo_type='2')['data']["algo_id"]
                    algo_id = swapAPI.take_order_algo(coin, '4', '1', '1', trigger_price=key_prices[list_length][0],
                                                      algo_type='2')['data']["algo_id"]
                    # 记录日志
                    algo = open('algo_id.txt', 'w')
                    algo.write('#######')
                    algo.write('\n')
                    algo.write(clock)
                    algo.write('\n')
                    algo.write(str(algo_id_1))
                    algo.write('\n')
                    algo.write(str(algo_id_2))
                    algo.write('\n')
                    algo.write(str(algo_id))
                    algo.write('\n')
                    algo.close()

                # cycle = 0
                anomaly_add = 1
                add_l += 1
                if add_l > close_ratio:
                    print('\n', '多头已补仓！', '平仓价：', round(close_price, dec), ' ', '完成补仓', int(add_l), '次',
                          ' ', '下次补仓价：', key_prices[int(add_l)][0])
                else:
                    print('\n', '多头已补仓！', '尚未达到可平仓仓位要求', '完成补仓', int(add_l), '次',
                          ' ', '下次补仓价：', key_prices[int(add_l)][0])
                # 记录日志
                add = open('add.txt', 'w')
                add.write('#######')
                add.write('\n')
                add.write(clock)
                add.write('\n')
                add.write(str(round(close_price, dec)))
                add.write('\n')
                add.write(str(add_l))
                add.write('\n')
                add.write(str(add_s))
                add.write('\n')
                add.close()

            # 上涨触发空头补仓
            elif best_price >= add_price_s and add_tri == 0:
                if error_6 == 1:
                    print('error_6!')
                    error_6 = 0
                # add_s_price = best_ask + (5 * mini_price)  # 补空价格为卖一价加上修正
                amount_s = add_p_position[int(add_s)]  # 补空张数
                # position_original = position_s  # 记录现有仓位
                swapAPI.take_order(coin, '2', '', str(amount_s), client_oid="", order_type='4',
                                   match_price='0')  # 空头补空
                time.sleep(0.3)  # 时延确保对方服务器数据及时更新
                positions = swapAPI.get_specific_position(coin)  # 单个合约持仓信息 （20次/2s）
                avg_s = float(positions['holding'][1]['avg_cost'])  # 空头开仓均价
                close_price = avg_s * (1 - modify_ratio * (1 - (add_l / 100)))  # 平仓价
                # 设定止损单
                if add_s == 0:
                    algo_id_1 = swapAPI.take_order_algo(coin, '4', '1', '1500',
                                                        trigger_price=key_prices[list_length][1],
                                                        algo_type='2')['data']["algo_id"]
                    algo_id_2 = swapAPI.take_order_algo(coin, '4', '1', '499', trigger_price=key_prices[list_length][1],
                                                        algo_type='2')['data']["algo_id"]
                    algo_id = swapAPI.take_order_algo(coin, '3', '1', '1', trigger_price=key_prices[list_length][1],
                                                      algo_type='2')['data']["algo_id"]
                    # 记录日志
                    algo = open('algo_id.txt', 'w')
                    algo.write('#######')
                    algo.write('\n')
                    algo.write(clock)
                    algo.write('\n')
                    algo.write(str(algo_id_1))
                    algo.write('\n')
                    algo.write(str(algo_id_2))
                    algo.write('\n')
                    algo.write(str(algo_id))
                    algo.write('\n')
                    algo.close()

                # cycle = 0
                anomaly_add = 1
                add_s += 1
                if add_s > close_ratio:
                    print('\n', '空头已补仓！', '平仓价：', round(close_price, dec), ' ', '完成补仓', int(add_s), '次',
                          ' ', '下次补仓价：', key_prices[int(add_s)][1])
                else:
                    print('\n', '空头已补仓！', '尚未达到可平仓仓位要求', '完成补仓', int(add_s), '次',
                          ' ', '下次补仓价：', key_prices[int(add_s)][1])
                # 记录日志
                add = open('add.txt', 'w')
                add.write('#######')
                add.write('\n')
                add.write(clock)
                add.write('\n')
                add.write(str(round(close_price, dec)))
                add.write('\n')
                add.write(str(add_l))
                add.write('\n')
                add.write(str(add_s))
                add.write('\n')
                add.close()

            # 价格回升触发多头全平
            elif add_l > close_ratio and close_tri == 0:  # 调整此处可以改变平仓动作
                if best_price >= close_price:
                    if error_7 == 1:
                        print('error_7!')
                        error_7 = 0
                    swapAPI.take_order(coin, '4', '', str(position_s), client_oid="",
                                       order_type='4', match_price='0')  # 空头平仓（先平亏损头寸，防止爆仓）
                    swapAPI.take_order(coin, '3', '', str(position_l), client_oid="",
                                       order_type='4', match_price='0')  # 多头平仓
                    # print('\n', '多头平仓：', sell_l, '', '空头平仓：', sell_s)
                    accounts = swapAPI.get_coin_account(coin)  # 单个币种合约账户信息 （当用户没有持仓时，保证金率为10000）（20次/2s）
                    equity = float(accounts['info']['equity'])  # 账户权益
                    equ = open('equity.txt', 'a')  # 记录余额
                    equ.write('#######')
                    equ.write('\n')
                    equ.write(clock)
                    equ.write('\n')
                    equ.write(str(equity))
                    equ.write('\n')
                    equ.close()
                    record = open('My Record.txt', 'w')  # 清空记录
                    record.write('')
                    record.close()
                    add = open('add.txt', 'w')  # 清空记录
                    add.write('')
                    add.close()
                    algo = open('algo_id.txt', 'w')  # 清空记录
                    algo.write('')
                    algo.close()
                    # 平仓后还原异常状态参数
                    anomaly_const = 0
                    anomaly_add = 0
                    # 平仓后撤掉策略单
                    swapAPI.cancel_algos(coin, [algo_id_1, algo_id_2, algo_id], '1')
                    return  # 平仓后结束程序

            # 价格回落触发空头全平
            elif add_s > close_ratio and close_tri == 0:  # 调整此处可以改变平仓动作
                if best_price <= close_price:
                    if error_8 == 1:
                        print('error_8!')
                        error_8 = 0
                    swapAPI.take_order(coin, '3', '', str(position_l), client_oid="",
                                       order_type='4', match_price='0')  # 多头平仓（先平亏损头寸，防止爆仓）
                    swapAPI.take_order(coin, '4', '', str(position_s), client_oid="",
                                       order_type='4', match_price='0')  # 空头平仓
                    # print('\n', '多头平仓：', sell_l, '', '空头平仓：', sell_s)
                    accounts = swapAPI.get_coin_account(coin)  # 单个币种合约账户信息 （当用户没有持仓时，保证金率为10000）（20次/2s）
                    equity = float(accounts['info']['equity'])  # 账户权益
                    equ = open('equity.txt', 'a')  # 记录余额
                    equ.write('#######')
                    equ.write('\n')
                    equ.write(clock)
                    equ.write('\n')
                    equ.write(str(equity))
                    equ.write('\n')
                    equ.close()
                    record = open('My Record.txt', 'w')
                    record.write('')
                    record.close()
                    add = open('add.txt', 'w')
                    add.write('')
                    add.close()
                    algo = open('algo_id.txt', 'w')
                    algo.write('')
                    algo.close()
                    # 平仓后还原异常状态
                    anomaly_const = 0
                    anomaly_add = 0
                    # 平仓后撤掉策略单
                    swapAPI.cancel_algos(coin, [algo_id_1, algo_id_2, algo_id], '1')
                    return  # 平仓后结束程序


@retry
def restart():
    global anomaly_const
    global anomaly_add
    global lever
    try:
        swap_my()
    except (requests.exceptions.ProxyError, requests.exceptions.RequestException, requests.exceptions.HTTPError,
            requests.exceptions.ConnectionError, requests.exceptions.SSLError, requests.exceptions.Timeout,
            requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.RetryError) as e:
        anomaly_const = 1
        print('\n', "错误信息：", e)
        restart()
    else:
        print('\n', '已平仓！')
        son_thread = threading.Thread(target=message_box)
        son_thread.start()
        time.sleep(10)  # 时延留下平仓后操作空间
        # 全自动交易时屏蔽掉下面的语句即可
        # win32api.MessageBox(0, "已平仓,点击确定继续建仓，或者你可以关闭程序", "提醒", win32con.MB_ICONWARNING)


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
        anomaly_const = 0  # 异常读取常数初始化
        anomaly_add = 0  # 补仓状态记录
        lever = 0  # 修改杠杆参数
        # reminder = -10  # 价格风险提示设置
        restart()
