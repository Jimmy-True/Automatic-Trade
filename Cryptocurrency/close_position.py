import ex.swap_api as swap
import datetime
import time

api_key = ""
secret_key = ""
passphrase = ""


def get_timestamp():
    now = datetime.datetime.now()
    t = now.isoformat("T", "milliseconds")
    return t + "Z"


swapAPI = swap.SwapAPI(api_key, secret_key, passphrase, False)
position_l = 0
position_s = 0
# 手动指定
coin = 'BTC-USDT-SWAP'
clock = get_timestamp()
switch = 0  # 指定平多或者平空（0空1多）

positions = swapAPI.get_specific_position(coin)  # 单个合约持仓信息 （20次/2s）
if switch == 0:
    position_s = int(positions['holding'][0]['position'])  # 空头持仓量
    sell_s = swapAPI.take_order(coin, '4', '', str(position_s), client_oid="",
                                order_type='4', match_price='0')  # 空头平仓
    print('空头已平：', sell_s)
elif switch == 1:
    position_l = int(positions['holding'][0]['position'])  # 多头持仓量
    sell_l = swapAPI.take_order(coin, '3', '', str(position_l), client_oid="",
                                order_type='4', match_price='0')  # 多头平仓
    print('多头已平：', sell_l)

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
