import ex.swap_api as swap
import logging
import datetime
import math
import win32api
import win32con
import os
import sys
import requests
from retrying import retry


log_format = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(filename='mylog-rest.json', filemode='a', format=log_format, level=logging.INFO)


def get_timestamp():
    # 获取时间戳
    now = datetime.datetime.now()
    t = now.isoformat("T", "milliseconds")
    return t + "Z"


# def message_box():
#     # 设置消息提示框内容
#     win32api.MessageBox(0, '已平仓，8秒后将继续建仓，如需停止请关闭进程', "提醒", win32con.MB_ICONWARNING)


def swap_my():
    # 设置全局代理
    os.environ['http_proxy'] = 'http://127.0.0.1:1711'
    os.environ['https_proxy'] = 'https://127.0.0.1:1711'
    try:
        response = requests.get('http://httpbin.org/get')
        # print(response.text)
    except requests.exceptions.ConnectionError as e:
        print('Error', e.args)
        sys.exit(0)

    # 设置全局变量
    global anomaly_const
    global anomaly_add
    global initial_tri

    # 手动激活以强制启动某些功能
    # initial_tri = 1  # 关闭初始化模块
    # anomaly_const = 1  # 启动恢复模块
    # anomaly_add = 1  # 手动启用异常恢复时，如果已发生加仓行为则启用此选项

    # 某些功能开关（0开1关）
    add_tri = 0  # 加仓动作开关

    print('anomaly_const:', anomaly_const, '\n', 'anomaly_add:', anomaly_add)

    # 永续合约API
    swapAPI = swap.SwapAPI(api_key, secret_key, passphrase, False)

    # 手动设置参数
    leverage = 50  # 杠杆（数值越大收益越高，excel）
    dec = 2  # 价格小数位数
    modify_ratio = 2  # 补仓价格修正系数
    coin = 'ETH-USDT-SWAP'  # 交易币种
    # 基准阶梯仓位设置（excel）
    position_stage = [5, 20, 35, 60, 85, 125, 170, 170, 125, 85, 60, 35, 20, 4]
    # 多头补仓价格因子设置（excel）
    p_l_stage = [0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.09, 0.13, 0.15, 0.17, 0.19, 0.21, 0.23]
    # 空头补仓价格因子设置（excel）
    p_s_stage = [0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.09, 0.13, 0.15, 0.17, 0.19, 0.21, 0.23]

    # 初始化参数
    add_l_price = 0  # 多头补仓价格计数初始化
    add_s_price = 0  # 空头补仓价格计数初始化
    add_l_position = 0  # 多头补仓计数初始化
    add_s_position = 0  # 空头补仓计数初始化
    key_prices = []  # 触发价格初始化
    cycle = 0  # 循环因子
    mini_price = math.pow(0.1, dec)  # 最小变动价格
    price_s = 0  # 空头建仓价格因子初始化
    price_l = 0  # 多头建仓价格因子初始化
    swapAPI.set_leverage(coin, leverage, 3)  # 设定某个合约的杠杆 （5次/2s）

    while cycle == 0:
        # timestamp
        clock = get_timestamp()
        # positions
        positions = swapAPI.get_specific_position(coin)  # 单个合约持仓信息 （20次/2s）
        position_l = int(positions['holding'][0]['position'])  # 多头持仓量
        position_s = int(positions['holding'][1]['position'])  # 空头持仓量
        avg_l_show = float(positions['holding'][0]['avg_cost'])  # 展示用多头开仓均价
        avg_s_show = float(positions['holding'][1]['avg_cost'])  # 展示用空头开仓均价
        # ticker
        tickers = swapAPI.get_specific_ticker(coin)  # 公共-获取某个ticker信息 （20次/2s）
        best_ask = float(tickers['best_ask'])  # 卖一价
        best_bid = float(tickers['best_bid'])  # 买一价
        best_price = (best_ask + best_bid) / 2  # 结算标准价

        # 初始化仓位
        if initial_tri == 0 and anomaly_const == 0:
            # positions
            positions = swapAPI.get_specific_position(coin)  # 单个合约持仓信息 （20次/2s）
            price_s = float(positions['holding'][0]['avg_cost'])  # 空头建仓因子价
            price_l = float(positions['holding'][1]['avg_cost'])  # 多头建仓因子价
            # 触发补仓价格
            key_prices = [[round((1-p_l_stage[0]) * price_s, dec), round((1+p_s_stage[0]) * price_l, dec)],
                          [round((1-p_l_stage[1]) * price_s, dec), round((1+p_s_stage[1]) * price_l, dec)],
                          [round((1-p_l_stage[2]) * price_s, dec), round((1+p_s_stage[2]) * price_l, dec)],
                          [round((1-p_l_stage[3]) * price_s, dec), round((1+p_s_stage[3]) * price_l, dec)],
                          [round((1-p_l_stage[4]) * price_s, dec), round((1+p_s_stage[4]) * price_l, dec)],
                          [round((1-p_l_stage[5]) * price_s, dec), round((1+p_s_stage[5]) * price_l, dec)],
                          [round((1-p_l_stage[6]) * price_s, dec), round((1+p_s_stage[6]) * price_l, dec)],
                          [round((1-p_l_stage[7]) * price_s, dec), round((1+p_s_stage[7]) * price_l, dec)],
                          [round((1-p_l_stage[8]) * price_s, dec), round((1+p_s_stage[8]) * price_l, dec)],
                          [round((1-p_l_stage[9]) * price_s, dec), round((1+p_s_stage[9]) * price_l, dec)],
                          [round((1-p_l_stage[10]) * price_s, dec), round((1+p_s_stage[10]) * price_l, dec)],
                          [round((1-p_l_stage[11]) * price_s, dec), round((1+p_s_stage[11]) * price_l, dec)],
                          [round((1-p_l_stage[12]) * price_s, dec), round((1+p_s_stage[12]) * price_l, dec)]]
            print('初始建仓完成！', '\n', '补仓价格列表：', key_prices)
            initial_tri = 1  # 初始化仓位完成
            # 记录日志
            record = open('My Record_Trend.txt', 'w')
            record.write('#######')
            record.write('\n')
            record.write(clock)
            record.write('\n')
            record.write(str(price_l))
            record.write('\n')
            record.write(str(price_s))
            record.write('\n')
            record.close()

        # 确保建仓完成
        elif position_l == 0 or position_s == 0:
            # 警告
            win32api.MessageBox(0, "初始建仓似乎没有完成，请检查确保仓位正确！", "注意", win32con.MB_ICONWARNING)
            sys.exit(0)

        # 恢复模块。异常发生后,恢复交易信息
        elif anomaly_const == 1:
            record = open('My Record_Trend.txt', 'r')
            init_record = record.readlines()
            price_s = float(init_record[-1])  # 空头建仓价格因子
            price_l = float(init_record[-2])  # 多头建仓价格因子

            # 恢复触发补仓价格列表
            key_prices = [[round((1-p_l_stage[0]) * price_s, dec), round((1+p_s_stage[0]) * price_l, dec)],
                          [round((1-p_l_stage[1]) * price_s, dec), round((1+p_s_stage[1]) * price_l, dec)],
                          [round((1-p_l_stage[2]) * price_s, dec), round((1+p_s_stage[2]) * price_l, dec)],
                          [round((1-p_l_stage[3]) * price_s, dec), round((1+p_s_stage[3]) * price_l, dec)],
                          [round((1-p_l_stage[4]) * price_s, dec), round((1+p_s_stage[4]) * price_l, dec)],
                          [round((1-p_l_stage[5]) * price_s, dec), round((1+p_s_stage[5]) * price_l, dec)],
                          [round((1-p_l_stage[6]) * price_s, dec), round((1+p_s_stage[6]) * price_l, dec)],
                          [round((1-p_l_stage[7]) * price_s, dec), round((1+p_s_stage[7]) * price_l, dec)],
                          [round((1-p_l_stage[8]) * price_s, dec), round((1+p_s_stage[8]) * price_l, dec)],
                          [round((1-p_l_stage[9]) * price_s, dec), round((1+p_s_stage[9]) * price_l, dec)],
                          [round((1-p_l_stage[10]) * price_s, dec), round((1+p_s_stage[10]) * price_l, dec)],
                          [round((1-p_l_stage[11]) * price_s, dec), round((1+p_s_stage[11]) * price_l, dec)],
                          [round((1-p_l_stage[12]) * price_s, dec), round((1+p_s_stage[12]) * price_l, dec)]]
            record.close()
            anomaly_const = 0  # 异常恢复完成
            if anomaly_add >= 1:
                add = open('add_Trend.txt', 'r')
                init_add = add.readlines()
                add_l_position = int(float(init_add[-4]))
                add_s_position = int(float(init_add[-3]))
                add_l_price = int(float(init_add[-2]))
                add_s_price = int(float(init_add[-1]))
                print('\n', clock, '程序已从异常中恢复！', '补仓价格列表：', key_prices,
                      '\n', '下次多头补仓价：', key_prices[int(add_l_price)][1],
                      '补仓数:', position_stage[int(add_l_position)], ' ',
                      '下次空头补仓价：', key_prices[int(add_s_price)][0],
                      '补仓数:', position_stage[int(add_s_position)])
                add.close()
            else:
                print('\n', clock, '程序已从异常中恢复！', '补仓价格列表：', key_prices)

        # 恢复失败，程序报错
        elif price_s == 0 or price_l == 0 or (anomaly_add == 1 and add_l_position == 0 and
                                              add_s_position == 0 and add_l_price == 0 and add_s_price == 0):
            # 警告
            win32api.MessageBox(0, "恢复失败，点击确定重试。", "注意", win32con.MB_ICONWARNING)
            sys.exit(0)

        # 仓位控制
        else:
            add_price_l = key_prices[int(add_l_price)][1]  # 触发补多价格
            add_price_s = key_prices[int(add_s_price)][0]  # 触发补空价格
            # monitor
            print('\r', clock, '当前价格：', round(best_price, dec), '多头开仓均价：', avg_l_show, '空头开仓均价：',
                  avg_s_show, '多头仓位：', position_l, '空头仓位：', position_s, '触发补多价格：', add_price_l, '触发补空价格:',
                  add_price_s, end='')

            # 上涨触发多头补仓空头减仓
            if best_ask >= add_price_l and add_tri == 0:
                amount_l = position_stage[int(add_l_position)]  # 仓位变化张数
                swapAPI.take_order(coin, '4', '', str(amount_l), client_oid="", order_type='4',
                                   match_price='0')  # 上涨减空
                swapAPI.take_order(coin, '1', '', str(amount_l), client_oid="", order_type='4',
                                   match_price='0')  # 上涨补多
                price_s = best_ask + (mini_price * modify_ratio)  # 此时的卖一价加上一定修正
                anomaly_add = 1
                add_l_position += 1
                add_l_price += 1
                add_s_price = 0
                if 0 <= add_s_position <= 2:
                    add_s_position = 0
                elif 3 <= add_s_position <= 4:
                    add_s_position -= 1
                elif 5 <= add_s_position <= 6:
                    add_s_position = 3
                elif 7 <= add_s_position <= 8:
                    add_s_position = 9
                elif 9 <= add_s_position <= 10:
                    add_s_position += 1
                elif 11 <= add_s_position <= 12:
                    add_s_position = 11
                # 更新触发空头补仓价格列表
                key_prices = [[round((1 - p_l_stage[0]) * price_s, dec), round((1 + p_s_stage[0]) * price_l, dec)],
                              [round((1 - p_l_stage[1]) * price_s, dec), round((1 + p_s_stage[1]) * price_l, dec)],
                              [round((1 - p_l_stage[2]) * price_s, dec), round((1 + p_s_stage[2]) * price_l, dec)],
                              [round((1 - p_l_stage[3]) * price_s, dec), round((1 + p_s_stage[3]) * price_l, dec)],
                              [round((1 - p_l_stage[4]) * price_s, dec), round((1 + p_s_stage[4]) * price_l, dec)],
                              [round((1 - p_l_stage[5]) * price_s, dec), round((1 + p_s_stage[5]) * price_l, dec)],
                              [round((1 - p_l_stage[6]) * price_s, dec), round((1 + p_s_stage[6]) * price_l, dec)],
                              [round((1 - p_l_stage[7]) * price_s, dec), round((1 + p_s_stage[7]) * price_l, dec)],
                              [round((1 - p_l_stage[8]) * price_s, dec), round((1 + p_s_stage[8]) * price_l, dec)],
                              [round((1 - p_l_stage[9]) * price_s, dec), round((1 + p_s_stage[9]) * price_l, dec)],
                              [round((1 - p_l_stage[10]) * price_s, dec), round((1 + p_s_stage[10]) * price_l, dec)],
                              [round((1 - p_l_stage[11]) * price_s, dec), round((1 + p_s_stage[11]) * price_l, dec)],
                              [round((1 - p_l_stage[12]) * price_s, dec), round((1 + p_s_stage[12]) * price_l, dec)]]
                print('\n', '多头已补仓！', '下次多头补仓价：', key_prices[int(add_l_price)][1],
                      '补仓数:', position_stage[int(add_l_position)], ' ',
                      '下次空头补仓价：', key_prices[int(add_s_price)][0],
                      '补仓数:', position_stage[int(add_s_position)])
                # 记录日志
                add = open('add_Trend.txt', 'w')
                add.write('#######')
                add.write('\n')
                add.write(clock)
                add.write('\n')
                add.write(str(add_l_position))
                add.write('\n')
                add.write(str(add_s_position))
                add.write('\n')
                add.write(str(add_l_price))
                add.write('\n')
                add.write(str(add_s_price))
                add.write('\n')
                add.close()

                record = open('My Record_Trend.txt', 'w')
                record.write('#######')
                record.write('\n')
                record.write(clock)
                record.write('\n')
                record.write(str(price_l))
                record.write('\n')
                record.write(str(price_s))
                record.write('\n')
                record.close()

            # 下跌触发空头补仓多头减仓
            elif best_bid <= add_price_s and add_tri == 0:
                amount_s = position_stage[int(add_s_position)]  # 仓位变化张数
                swapAPI.take_order(coin, '3', '', str(amount_s), client_oid="", order_type='4',
                                   match_price='0')  # 下跌减多
                swapAPI.take_order(coin, '2', '', str(amount_s), client_oid="", order_type='4',
                                   match_price='0')  # 下跌补空
                price_l = best_bid - (mini_price * modify_ratio)  # 此时的买一价减去一定修正
                anomaly_add = 1
                add_s_position += 1
                add_s_price += 1
                add_l_price = 0
                if 0 <= add_l_position <= 2:
                    add_l_position = 0
                elif 3 <= add_l_position <= 4:
                    add_l_position -= 1
                elif 5 <= add_l_position <= 6:
                    add_l_position = 3
                elif 7 <= add_l_position <= 8:
                    add_l_position = 9
                elif 9 <= add_l_position <= 10:
                    add_l_position += 1
                elif 11 <= add_l_position <= 12:
                    add_l_position = 11
                # 更新触发多头补仓价格列表
                key_prices = [[round((1 - p_l_stage[0]) * price_s, dec), round((1 + p_s_stage[0]) * price_l, dec)],
                              [round((1 - p_l_stage[1]) * price_s, dec), round((1 + p_s_stage[1]) * price_l, dec)],
                              [round((1 - p_l_stage[2]) * price_s, dec), round((1 + p_s_stage[2]) * price_l, dec)],
                              [round((1 - p_l_stage[3]) * price_s, dec), round((1 + p_s_stage[3]) * price_l, dec)],
                              [round((1 - p_l_stage[4]) * price_s, dec), round((1 + p_s_stage[4]) * price_l, dec)],
                              [round((1 - p_l_stage[5]) * price_s, dec), round((1 + p_s_stage[5]) * price_l, dec)],
                              [round((1 - p_l_stage[6]) * price_s, dec), round((1 + p_s_stage[6]) * price_l, dec)],
                              [round((1 - p_l_stage[7]) * price_s, dec), round((1 + p_s_stage[7]) * price_l, dec)],
                              [round((1 - p_l_stage[8]) * price_s, dec), round((1 + p_s_stage[8]) * price_l, dec)],
                              [round((1 - p_l_stage[9]) * price_s, dec), round((1 + p_s_stage[9]) * price_l, dec)],
                              [round((1 - p_l_stage[10]) * price_s, dec), round((1 + p_s_stage[10]) * price_l, dec)],
                              [round((1 - p_l_stage[11]) * price_s, dec), round((1 + p_s_stage[11]) * price_l, dec)],
                              [round((1 - p_l_stage[12]) * price_s, dec), round((1 + p_s_stage[12]) * price_l, dec)]]
                print('\n', '空头已补仓！', '下次多头补仓价：', key_prices[int(add_l_price)][1],
                      '补仓数:', position_stage[int(add_l_position)], ' ',
                      '下次空头补仓价：', key_prices[int(add_s_price)][0],
                      '补仓数:', position_stage[int(add_s_position)])
                # 记录日志
                add = open('add_Trend.txt', 'w')
                add.write('#######')
                add.write('\n')
                add.write(clock)
                add.write('\n')
                add.write(str(add_l_position))
                add.write('\n')
                add.write(str(add_s_position))
                add.write('\n')
                add.write(str(add_l_price))
                add.write('\n')
                add.write(str(add_s_price))
                add.write('\n')
                add.close()

                record = open('My Record_Trend.txt', 'w')
                record.write('#######')
                record.write('\n')
                record.write(clock)
                record.write('\n')
                record.write(str(price_l))
                record.write('\n')
                record.write(str(price_s))
                record.write('\n')
                record.close()


@retry
def restart():
    global anomaly_const
    global anomaly_add
    global initial_tri
    try:
        swap_my()
    except (requests.exceptions.ProxyError, requests.exceptions.RequestException, requests.exceptions.HTTPError,
            requests.exceptions.ConnectionError, requests.exceptions.SSLError, requests.exceptions.Timeout,
            requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout, requests.exceptions.RetryError) as e:
        anomaly_const = 1
        print('\n', "错误信息：", e)
        restart()


if __name__ == '__main__':

    # 设置子账户API密码

    # # Watch_Only
    api_key = ""
    secret_key = ""
    passphrase = ""

    # # Trade_Allowed
    api_key = ""
    secret_key = ""
    passphrase = ""

    # 该策略仅进行仓位控制，需要手动建仓与平仓
    while 1:
        anomaly_const = 0  # 异常读取常数初始化
        anomaly_add = 0  # 补仓状态记录
        initial_tri = 0  # 初始化控制开关
        restart()
