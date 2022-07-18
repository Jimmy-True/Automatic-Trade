import ex.futures_api as future
import ex.spot_api as spot
import os


# 设置全局代理
os.environ['http_proxy'] = 'http://127.0.0.1:1711'
os.environ['https_proxy'] = 'https://127.0.0.1:1711'
# Watch_Only
api_key = ""
secret_key = ""
passphrase = ""
futuresAPI = future.FutureAPI(api_key, secret_key, passphrase, False)
spotAPI = spot.SpotAPI(api_key, secret_key, passphrase, False)
coin = 'BTC-USD-210326'  # 交易币种
coin_spot = 'BTC-USDT'
underlying = 'BTC-USD'  # 交易币种
value = 100  # 一张合约价值（单位$）
# coin = 'ETH-USD-210326'  # 交易币种
# coin_spot = 'ETH-USDT'
# underlying = 'ETH-USD'  # 交易币种
# value = 10  # 一张合约价值（单位$）
# check times
position = futuresAPI.get_specific_position(coin)
tickers = spotAPI.get_specific_ticker(coin_spot)  # 公共-获取某个ticker信息 （20次/2s）
best_ask = float(tickers['best_ask'])  # 卖一价
best_bid = float(tickers['best_bid'])  # 买一价
best_price = (best_ask + best_bid) / 2  # 结算标准价
equity = float(futuresAPI.get_coin_account(underlying)['equity']) * best_price  # 账户价值
position_long = float(position['holding'][0]['long_qty']) * value  # 多头仓位价值
position_short = float(position['holding'][0]['short_qty']) * value  # 空头仓位价值
long_ratio = round(1 + position_long / equity, 2)  # 多头倍数
short_ratio = round(position_short / equity, 2)  # 空头倍数
net_ratio = round(abs(long_ratio - short_ratio), 2)  # 净倍数
net_position = round(equity * net_ratio, 2)  # 净倍数美元
if long_ratio >= short_ratio:
    # '账户价值：', round(equity, 2), '$', ' ',
    print('多头：', long_ratio, '倍', ' ', '空头：', short_ratio, '倍', ' ',
          '净', net_ratio, '倍多', ' ', '约为', net_position, '$')
else:
    # '账户价值：', round(equity, 2), '$',
    print(' ', '多头：', long_ratio, '倍', ' ', '空头：', short_ratio, '倍', ' ',
          '净', net_ratio, '倍空', ' ', '约为', net_position, '$')