from requests_html import HTMLSession
import os
import sys
import requests
import csv
import datetime


def get_timestamp():
    now = datetime.datetime.now()
    t = now.isoformat("T", "milliseconds")
    return t + "Z"


# # 设置全局代理
# os.environ['http_proxy'] = 'http://127.0.0.1:1711'
# os.environ['https_proxy'] = 'https://127.0.0.1:1711'
# try:
#     response = requests.get('http://httpbin.org/get')
#     # print(response.text)
# except requests.exceptions.ConnectionError as e:
#     print('Error', e.args)
#     sys.exit(0)


session = HTMLSession()
send_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36",
    "Connection": "keep-alive",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.8"}
url = 'https://www.macromicro.me/collections/9/us-market-relative/48/target-rate'
r = session.get(url, headers=send_headers)
# 巴菲特指数
Buffett_sel = '#ccidx-9-1 > div:nth-child(1) > article:nth-child(2) > div:nth-child(1) > div:nth-child(2) > ul:nth-child(2) > li:nth-child(1) > div:nth-child(3) > span:nth-child(1)'
Buffett = round(float((r.html.find(Buffett_sel))[0].text.replace(',', '')) / 5000, 5)
# 长短期国债
national_debt_sel = '#ccidx-9-5 > div:nth-child(1) > article:nth-child(2) > div:nth-child(1) > div:nth-child(2) > ul:nth-child(2) > li:nth-child(3) > div:nth-child(3) > span:nth-child(1)'
national_debt = round(float((r.html.find(national_debt_sel))[0].text.replace(',', '')) / 100, 4)
print(Buffett, national_debt)
# OFR金融压力指数
OFR_sel = '#ccidx-9-14 > div:nth-child(1) > article:nth-child(2) > div:nth-child(1) > div:nth-child(2) > ul:nth-child(2) > li:nth-child(4) > div:nth-child(3) > span:nth-child(1)'
OFR = round(float((r.html.find(OFR_sel))[0].text.replace(',', '')) / 1000, 4)
# 隔夜Libor
Libor_sel = '#ccidx-9-11 > div:nth-child(1) > article:nth-child(2) > div:nth-child(1) > div:nth-child(2) > ul:nth-child(2) > li:nth-child(1) > div:nth-child(3) > span:nth-child(1)'
Libor = float((r.html.find(Libor_sel))[0].text.replace(',', '')) / 100
# 美德利差
debet_interest_margin_sel = '#ccidx-9-13 > div:nth-child(1) > article:nth-child(2) > div:nth-child(1) > div:nth-child(2) > ul:nth-child(2) > li:nth-child(1) > div:nth-child(3) > span:nth-child(1)'
debet_interest_margin = -1 * float((r.html.find(debet_interest_margin_sel))[0].text.replace(',', '')) / 100
# FED资产比GDP
url = 'https://sc.macromicro.me/charts/1244/us-fed-assets-ngdp'
r = session.get(url, headers=send_headers)
FED_GDP_sel = 'div.sidebar-box-block:nth-child(2) > ul:nth-child(2) > li:nth-child(1) > div:nth-child(3) > span:nth-child(1)'
FED_GDP = round(float((r.html.find(FED_GDP_sel))[0].text.replace(',', '')) / 20000, 4)
# 美国核心通货膨胀率
url = 'https://www.macromicro.me/charts/10/cpi'
r = session.get(url, headers=send_headers)
cpi_sel = 'div.sidebar-box-block:nth-child(2) > ul:nth-child(2) > li:nth-child(2) > div:nth-child(3) > span:nth-child(1)'
cpi = round(float((r.html.find(cpi_sel))[0].text.replace(',', '')) / 100, 4)
print(Buffett, national_debt, OFR, FED_GDP, Libor, debet_interest_margin, cpi)
clock = get_timestamp()
with open("Economic.csv", "a") as csvfile:
    writer = csv.writer(csvfile)
    # 先写入columns_name
    writer.writerow(['time', 'Buffett', 'national_debt', 'OFR', 'FED_GDP', 'Libor', 'debet_interest_margin', 'cpi'])
    # 写入多行用writerows
    writer.writerow([clock, Buffett, national_debt, OFR, FED_GDP, Libor, debet_interest_margin, cpi])
