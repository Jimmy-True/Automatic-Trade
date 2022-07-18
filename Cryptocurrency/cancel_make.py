import math
import ex.swap_api as swap
import time


coin = 'BTC-USDT-SWAP'
# Trade_Allowed
api_key = ""
secret_key = ""
passphrase = ""
# 永续合约API
swapAPI = swap.SwapAPI(api_key, secret_key, passphrase, False)
unit_batch_cancel_amount = 10
position_amount = [24]
total = 24
# 撤限价单
position_total = 0
id_list = []
# 对列表元素求和
for m in position_amount:
    if type(m) is list:
        for n in m:
            if type(n) is int:
                position_total += n
    elif type(m) is int:
        position_total += m
print(position_total)
batch_cancel_amount = math.ceil(position_total / unit_batch_cancel_amount)  # 批量撤单次数
print(batch_cancel_amount)
i = 0
idr = open(r'Path of ids.txt', 'r')
idr_record = idr.readlines()
idr.close()
while i < batch_cancel_amount:
    j = 0
    id_list = []
    index = total - unit_batch_cancel_amount * i
    print(index)
    if index > 10:
        index = 10
    else:
        index = index
    print(index)
    while j < index:
        id_list.append(str(idr_record[j + i * unit_batch_cancel_amount]).replace('\n', '').replace('\r', ''))
        j += 1
    print(id_list)
    result = swapAPI.revoke_orders(coin, ids=id_list)
    time.sleep(0.5)
    print(result)
    i += 1
# 撤策略单
algor_amount = open(r'Path of algo_amount.txt', 'r')
algo_amount = int(algor_amount.readlines()[0])
algor_amount.close()
algor = open(r'Path of algo_id.txt', 'r')
algo_record = algor.readlines()
algor.close()
i = 0
while i <= algo_amount:
    algo_id = str(algo_record[i]).replace('\n', '').replace('\r', '')  # 策略单id
    # 撤掉策略单
    result = swapAPI.cancel_algos(coin, [algo_id], '1')
    print(result)
    i += 1
record = open(r'Path of equity_init.txt', 'w')  # 清空记录
record.write('')
record.close()
add = open(r'Path of algo_amount.txt', 'w')  # 清空记录
add.write('')
add.close()
algo = open(r'Path of algo_id.txt', 'w')  # 清空记录
algo.write('')
algo.close()
idr = open(r'Path of ids.txt', 'w')  # 清空记录
idr.write('')
idr.close()

