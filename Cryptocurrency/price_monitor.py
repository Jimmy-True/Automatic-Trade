import requests
import ex.swap_api as swap
import os
import sys
import tkinter as tk  # 使用Tkinter前需要先导入


def price_monitor():
    while 1:
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

        # 永续合约API
        swapAPI = swap.SwapAPI(api_key, secret_key, passphrase, False)
        # 参数
        coin = 'BTC-USDT-SWAP'
        dec = 1  # 价格小数位数
        # price
        tickers = swapAPI.get_specific_ticker(coin)
        best_ask = float(tickers['best_ask'])  # 卖一价
        best_bid = float(tickers['best_bid'])  # 买一价
        best_price = round((best_ask + best_bid) / 2, dec)  # 结算标准价

        # 第1步，实例化object，建立窗口window
        window = tk.Tk()

        # 第2步，给窗口的可视化起名字
        window.title(coin + 'Price')

        # 第3步，设定窗口的大小(长 * 宽)
        window.geometry('500x300')  # 这里的乘是小x

        # 第4步，在图形界面上设定标签
        var = tk.StringVar()  # 将label标签的内容设置为字符类型，用var来接收hit_me函数的传出内容用以显示在标签上
        l = tk.Label(window, textvariable=var, bg='green', fg='white', font=('Arial', 12), width=30, height=2)
        # 说明： bg为背景，fg为字体颜色，font为字体，width为长，height为高，这里的长和高是字符的长和高，比如height=2,就是标签有2个字符这么高
        l.pack()

        var.set(str(best_price))

        # 第5步，主窗口循环显示
        window.mainloop()


if __name__ == '__main__':

    # 设置API密码

    # Watch_Only
    api_key = ""
    secret_key = ""
    passphrase = ""

    tri_l = 0
    tri_s = 0
    price_monitor()

