import os
import sys
import requests
import win32api
import win32con
import re
import time
import datetime
import csv
from requests_html import HTMLSession
from selenium import webdriver
from selenium.webdriver.firefox.options import Options


# # 设置全局代理
# os.environ['http_proxy'] = 'http://127.0.0.1:1711'
# os.environ['https_proxy'] = 'https://127.0.0.1:1711'
# try:
#     response = requests.get('http://httpbin.org/get')
#     # print(response.text)
# except requests.exceptions.ConnectionError as e:
#     print('Error', e.args)
#     sys.exit(0)


def get_timestamp():
    now = datetime.datetime.now()
    t = now.isoformat("T", "milliseconds")
    return t + "Z"


def predict_sum(parm_1, parm_2, parm_3, parm_4):  # 数据由新到旧,预测年度值,季度数字求和为年度数字时使用
    slope = ((1.05 * (parm_1 - parm_4) / parm_4) + (parm_2 - parm_3) / parm_3 + (0.95 * (parm_3 - parm_4) / parm_4)) / 3
    predicter_1 = round(4 * parm_1 * (1 + slope))
    predicter_2 = 1.2 * parm_1 + 1.05 * parm_2 + 0.95 * parm_3 + 0.8 * parm_4
    if (0.5 * predicter_2) <= predicter_1 <= (1.5 * predicter_2):
        predicter = predicter_1
    else:
        predicter = 1.05 * predicter_2
    return predicter


def predict(parm_1, parm_2, parm_3, parm_4):  # 数据由新到旧,预测年度值,季度数字为年度数字时使用
    slope = ((1.05 * (parm_1 - parm_4) / parm_4) + (parm_2 - parm_3) / parm_3 + (0.95 * (parm_3 - parm_4) / parm_4)) / 3
    predicter_1 = round(parm_1 * (1 + slope))
    predicter_2 = (1.2 * parm_1 + 1.05 * parm_2 + 0.95 * parm_3 + 0.8 * parm_4) / 4
    if (0.6 * predicter_2) <= predicter_1 <= (1.4 * predicter_2):
        predicter = predicter_1
    else:
        predicter = 1.05 * predicter_2
    return predicter


def crawler(stock_code, stock_name, timer, ex_ratio, beneish, pe_tri):  # 股票代码，数据类型，程序反应间隔,汇率
    stock_code = stock_code.upper()
    stock_name = stock_name.lower()
    session = HTMLSession()
    send_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36",
        "Connection": "keep-alive",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.8"}
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36"


    # PE
    if pe_tri == 1:
        url = 'https://www.macrotrends.net/stocks/charts/' + stock_code + '/' + stock_name + '/pe-ratio'
        r = session.get(url, headers=send_headers)
        sel_1 = '#style-1 > table:nth-child(1) > tbody:nth-child(3) > tr:nth-child(1) > td:nth-child(4)'
        sel_2 = '#style-1 > table:nth-child(1) > tbody:nth-child(3) > tr:nth-child(2) > td:nth-child(4)'
        sel_3 = '#style-1 > table:nth-child(1) > tbody:nth-child(3) > tr:nth-child(3) > td:nth-child(4)'
        sel_4 = '#style-1 > table:nth-child(1) > tbody:nth-child(3) > tr:nth-child(4) > td:nth-child(4)'
        sel_5 = '#style-1 > table:nth-child(1) > tbody:nth-child(3) > tr:nth-child(5) > td:nth-child(4)'
        sel_6 = '#style-1 > table:nth-child(1) > tbody:nth-child(3) > tr:nth-child(6) > td:nth-child(4)'
        sel_7 = '#style-1 > table:nth-child(1) > tbody:nth-child(3) > tr:nth-child(7) > td:nth-child(4)'
        sel_8 = '#style-1 > table:nth-child(1) > tbody:nth-child(3) > tr:nth-child(8) > td:nth-child(4)'
        sel_9 = '#style-1 > table:nth-child(1) > tbody:nth-child(3) > tr:nth-child(9) > td:nth-child(4)'
        sel_10 = '#style-1 > table:nth-child(1) > tbody:nth-child(3) > tr:nth-child(10) > td:nth-child(4)'
        sel_11 = '#style-1 > table:nth-child(1) > tbody:nth-child(3) > tr:nth-child(11) > td:nth-child(4)'
        sel_12 = '#style-1 > table:nth-child(1) > tbody:nth-child(3) > tr:nth-child(12) > td:nth-child(4)'
        pe_1 = float((r.html.find(sel_1))[0].text.replace(',', ''))
        pe_2 = float((r.html.find(sel_2))[0].text.replace(',', ''))
        pe_3 = float((r.html.find(sel_3))[0].text.replace(',', ''))
        pe_4 = float((r.html.find(sel_4))[0].text.replace(',', ''))
        pe_5 = float((r.html.find(sel_5))[0].text.replace(',', ''))
        pe_6 = float((r.html.find(sel_6))[0].text.replace(',', ''))
        pe_7 = float((r.html.find(sel_7))[0].text.replace(',', ''))
        pe_8 = float((r.html.find(sel_8))[0].text.replace(',', ''))
        pe_9 = float((r.html.find(sel_9))[0].text.replace(',', ''))
        pe_10 = float((r.html.find(sel_10))[0].text.replace(',', ''))
        pe_11 = float((r.html.find(sel_11))[0].text.replace(',', ''))
        pe_12 = float((r.html.find(sel_12))[0].text.replace(',', ''))
        pe = round((pe_1 + pe_2 + pe_3 + pe_4 + pe_5 + pe_6 + pe_7 + pe_8 + pe_9 + pe_10 + pe_11 + pe_12) / 12, 2)
    else:
        pe = 0
    print('pe:', pe)


    # statistics
    url = ('https://finance.yahoo.com/quote/' + stock_code + '/key-statistics?p=' + stock_code)
    r = session.get(url, headers=send_headers)
    price_sel = 'span.Trsdu\(0\.3s\):nth-child(1)'
    beta_sel = 'div.Pstart\(20px\) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > table:nth-child(2) > tbody:nth-child(1) > tr:nth-child(1) > td:nth-child(2)'
    float_sel = 'div.Pstart\(20px\) > div:nth-child(2) > div:nth-child(1) > div:nth-child(1) > table:nth-child(2) > tbody:nth-child(1) > tr:nth-child(5) > td:nth-child(2)'
    if ex_ratio == 1:
        roa_sel = 'div.Fl\(start\):nth-child(3) > div:nth-child(2) > div:nth-child(3) > div:nth-child(1) > div:nth-child(1) > table:nth-child(2) > tbody:nth-child(1) > tr:nth-child(1) > td:nth-child(2)'
    else:
        roa_sel = 'div.Mb\(10px\):nth-child(3) > div:nth-child(3) > div:nth-child(1) > div:nth-child(1) > table:nth-child(2) > tbody:nth-child(1) > tr:nth-child(1) > td:nth-child(2)'
    divi_yield_sel = 'div.Pstart\(20px\) > div:nth-child(3) > div:nth-child(1) > div:nth-child(1) > table:nth-child(2) > tbody:nth-child(1) > tr:nth-child(2) > td:nth-child(2)'
    divi_payout_sel = 'div.Pstart\(20px\) > div:nth-child(3) > div:nth-child(1) > div:nth-child(1) > table:nth-child(2) > tbody:nth-child(1) > tr:nth-child(6) > td:nth-child(2)'
    # 现价
    price_current = (r.html.find(price_sel))[0].text.replace(',', '')
    # if price_current == '直播:':
    #     price_sel = '.Fz\(36px\)'
    #     price_current = float((r.html.find(price_sel))[0].text.replace(',', ''))
    # else:
    price_current = float(price_current)
    # beta值
    if (r.html.find(beta_sel))[0].text == 'N/A':
        beta = 1
    else:
        beta = float((r.html.find(beta_sel))[0].text)
    # 流通股份
    float_share_amount = (r.html.find(float_sel))[0].text
    float_share_amount_list = list(float_share_amount)
    if float_share_amount_list[-1] == 'B':
        float_share_amount = float(float(float_share_amount.rstrip('B')) * 1000000)
    elif float_share_amount_list[-1] == 'M':
        float_share_amount = float(float(float_share_amount.rstrip('M')) * 1000)
    else:
        # 设置消息提示框内容
        win32api.MessageBox(0, '已发行股份单位有误', "提醒", win32con.MB_ICONWARNING)
        sys.exit(0)
    # 资产回报率 (过去十二个月)
    roa = (r.html.find(roa_sel))[0].text.rstrip('%').replace(',', '')
    if roa == 'N/A':
        roa = 0
    else:
        roa = round(float(roa) / 100, 4)
    # 预测年度股息收益率
    divi_yield = (r.html.find(divi_yield_sel))[0].text
    if divi_yield == 'N/A':
        divi_yield = 0
    else:
        divi_yield = round(float(divi_yield.rstrip('%').replace(',', '')) / 100, 4)
    # 派息率
    divi_payout = (r.html.find(divi_payout_sel))[0].text
    if divi_payout == 'N/A':
        divi_payout = 0
    else:
        divi_payout = round(float(divi_payout.rstrip('%').replace(',', '')) / 100, 4)
    # 返回结果
    print('price_current:', price_current, 'beta:', beta, 'float_share_amount:', float_share_amount, 'roa:', roa, 'divi_yield:',
          divi_yield, 'divi_payout:', divi_payout)
    time.sleep(1)


    # financials
    url = ('https://finance.yahoo.com/quote/' + stock_code + '/financials?p=' + stock_code)

    # 季度毛利
    if beneish == 1:
        r = session.get(url, headers=send_headers)
        gross_sel_1 = '.D\(tbrg\) > div:nth-child(3) > div:nth-child(1) > div:nth-child(3) > span:nth-child(1)'
        gross_sel_2 = '.D\(tbrg\) > div:nth-child(3) > div:nth-child(1) > div:nth-child(4) > span:nth-child(1)'
        gross_1 = float((r.html.find(gross_sel_1))[0].text.replace(',', ''))
        gross_2 = float((r.html.find(gross_sel_2))[0].text.replace(',', ''))

    firefox_options = Options()
    firefox_options.add_argument("--headless")  # define headless
    firefox_options.add_argument('--user-agent=%s' % user_agent)
    driver = webdriver.Firefox(options=firefox_options)  # 设置不打开网页,并伪装浏览器
    driver.get(url)  # 打开相应网页
    d = driver.page_source  # 获取网页html文件
    match = re.findall(r'Yahoo is part of (.*?) Media', d)
    # 判断是否有欢迎页面
    if match == ['Verizon']:
        driver.find_element_by_name("agree").click()
    d = driver.page_source  # 获取网页html文件
    driver.close()

    if beneish == 1:
        match = re.findall(r'"netIncomeFromContinuingOps":{"raw":(.*?),"fmt":"(.*?)","longFmt":"(.*?)"}', d)
        # 预测连续营业收入
        income_cops_1 = float(match[0][0]) / 1000
        income_cops_2 = float(match[1][0]) / 1000
        income_cops_3 = float(match[1][0]) / 1000
        income_cops_4 = float(match[1][0]) / 1000
        income_cops = predict_sum(income_cops_1, income_cops_2, income_cops_3, income_cops_4) / ex_ratio

        match = re.findall(r'"sellingGeneralAdministrative":{"raw":(.*?),"fmt":"(.*?)","longFmt":"(.*?)"}', d)
        # 销售总务及行政费用
        administrative_1 = float(match[0][0]) / 1000
        administrative_2 = float(match[1][0]) / 1000

    match = re.findall(r'"researchDevelopment":{"raw":(.*?),"fmt":"(.*?)","longFmt":"(.*?)"}', d)
    if len(match) <= 3:
        rd_ratio = 0
    else:
        rd_1 = round(float(match[-4][0]) / 1000 / ex_ratio)
        rd_2 = round(float(match[-3][0]) / 1000 / ex_ratio)
        rd_3 = round(float(match[-2][0]) / 1000 / ex_ratio)
        rd_4 = round(float(match[-1][0]) / 1000 / ex_ratio)
        rd_ratio = round((1.05 * (rd_1 - rd_2) / rd_2 + (rd_2 - rd_3) / rd_3 + 0.95 * (rd_3 - rd_4) / rd_4) / 3, 4)
    # 年度总收益
    match = re.findall(r'"totalRevenue":{"raw":(.*?),"fmt":"(.*?)","longFmt":"(.*?)"}', d)
    total_revenue_1 = round(float(match[-4][0]) / 1000 / ex_ratio)
    total_revenue_2 = round(float(match[-3][0]) / 1000 / ex_ratio)
    total_revenue_3 = round(float(match[-2][0]) / 1000 / ex_ratio)
    total_revenue_4 = round(float(match[-1][0]) / 1000 / ex_ratio)
    print('total_revenue_annual:', total_revenue_1, total_revenue_2, total_revenue_3, total_revenue_4)
    # 年度净收益
    match = re.findall(r'"earnings":{"raw":(.*?),"fmt":"(.*?)","longFmt":"(.*?)"}', d)
    total_earning_1 = round(float(match[3][0]) / 1000 / ex_ratio)
    total_earning_2 = round(float(match[2][0]) / 1000 / ex_ratio)
    total_earning_3 = round(float(match[1][0]) / 1000 / ex_ratio)
    total_earning_4 = round(float(match[0][0]) / 1000 / ex_ratio)
    print('total_earning_annual:', total_earning_1, total_earning_2, total_earning_3, total_earning_4)

    # # 切换到季度表
    # driver.find_element_by_xpath("//div[@id='Col1-1-Financials-Proxy']/section/div/div[2]/button/div/span").click()
    # time.sleep(timer)
    # d = driver.page_source  # 获取网页html文件
    # driver.close()

    match = re.findall(r'"totalRevenue":{"raw":(.*?),"fmt":"(.*?)","longFmt":"(.*?)"}', d)
    # 近四季度收益
    revenue_1 = round(float(match[0][0]) / 1000)
    revenue_2 = round(float(match[1][0]) / 1000)
    revenue_3 = round(float(match[2][0]) / 1000)
    revenue_4 = round(float(match[3][0]) / 1000)
    # print(revenue_1, revenue_2, revenue_3, revenue_4)
    # return
    # 预测总收益
    revenue = round(predict_sum(revenue_1, revenue_2, revenue_3, revenue_4) / ex_ratio)
    if beneish == 1:
        # 毛利率指数
        GMI = (gross_2 / revenue_2) / (gross_1 / revenue_1)
        # 营业收入指数
        SGI = revenue_1 / revenue_2
        # 销售管理费用指数
        SGAI = (administrative_1 / revenue_1) / (administrative_2 / revenue_2)

    match = re.findall(r'"earnings":{"raw":(.*?),"fmt":"(.*?)","longFmt":"(.*?)"}', d)
    # 近四季度净收益
    earnings_1 = round(float(match[-1][0]) / 1000)
    earnings_2 = round(float(match[-2][0]) / 1000)
    earnings_3 = round(float(match[-3][0]) / 1000)
    earnings_4 = round(float(match[-4][0]) / 1000)
    # 预测净收益
    earning = round(predict_sum(earnings_1, earnings_2, earnings_3, earnings_4) / ex_ratio)
    print('revenue:', revenue, 'earning:', earning, 'R&D:', rd_ratio, 'revenue_quarterly:', revenue_1,
          revenue_2, revenue_3, revenue_4, 'earnings_quarterly:', earnings_1, earnings_2, earnings_3, earnings_4)
    time.sleep(1)


    # balance_sheet
    url = ('https://hk.finance.yahoo.com/quote/' + stock_code + '/balance-sheet?p=' + stock_code)

    if beneish == 1:
        r = session.get(url, headers=send_headers)
        # 设备总值
        factory_sel_1 = '.D\(tbrg\) > div:nth-child(1) > div:nth-child(2) > div:nth-child(2) > div:nth-child(2) > div:nth-child(1) > div:nth-child(2) > div:nth-child(1) > div:nth-child(1) > div:nth-child(2) > span:nth-child(1)'
        factory_sel_2 = '.D\(tbrg\) > div:nth-child(1) > div:nth-child(2) > div:nth-child(2) > div:nth-child(2) > div:nth-child(1) > div:nth-child(2) > div:nth-child(1) > div:nth-child(1) > div:nth-child(3) > span:nth-child(1)'
        factory_1 = float((r.html.find(factory_sel_1))[0].text.replace(',', ''))
        factory_2 = float((r.html.find(factory_sel_2))[0].text.replace(',', ''))

        # 折旧
        old_sel_1 = '.D\(tbrg\) > div:nth-child(1) > div:nth-child(2) > div:nth-child(2) > div:nth-child(2) > div:nth-child(1) > div:nth-child(2) > div:nth-child(2) > div:nth-child(1) > div:nth-child(2) > span:nth-child(1)'
        old_sel_2 = '.D\(tbrg\) > div:nth-child(1) > div:nth-child(2) > div:nth-child(2) > div:nth-child(2) > div:nth-child(1) > div:nth-child(2) > div:nth-child(2) > div:nth-child(1) > div:nth-child(3) > span:nth-child(1)'
        old_1 = float((r.html.find(old_sel_1))[0].text.replace(',', ''))
        old_2 = float((r.html.find(old_sel_2))[0].text.replace(',', ''))

        # 折旧率指数
        DEPI = (old_2 / factory_2) / (old_1 / factory_1)

    url = ('https://finance.yahoo.com/quote/' + stock_code + '/balance-sheet?p=' + stock_code)
    firefox_options = Options()
    firefox_options.add_argument("--headless")  # define headless
    firefox_options.add_argument('--user-agent=%s' % user_agent)
    driver = webdriver.Firefox(options=firefox_options)  # 设置不打开网页,并伪装浏览器
    driver.get(url)  # 打开相应网页
    d = driver.page_source  # 获取网页html文件
    match = re.findall(r'Yahoo is part of (.*?) Media', d)
    # 判断是否有欢迎页面
    if match == ['Verizon']:
        driver.find_element_by_name("agree").click()
    driver.find_element_by_xpath("//div[@id='Col1-1-Financials-Proxy']/section/div/div[2]/button/div/span").click()
    time.sleep(timer)
    d = driver.page_source  # 获取网页html文件
    driver.close()

    if beneish == 1:
        match = re.findall(r'"netReceivables":{"raw":(.*?),"fmt":"(.*?)","longFmt":"(.*?)"}', d)
        # 应收账款净额
        receivable_1 = float(match[0][0]) / 1000
        receivable_2 = float(match[1][0]) / 1000
        # 应收账款指数
        DSRI = (receivable_1 / revenue_1) / (receivable_2 / revenue_2)

    match = re.findall(r'"cash":{"raw":(.*?),"fmt":"(.*?)","longFmt":"(.*?)"}', d)
    # 近四季现金
    cash_1 = float(match[0][0]) / 1000
    cash_2 = float(match[1][0]) / 1000
    cash_3 = float(match[2][0]) / 1000
    cash_4 = float(match[3][0]) / 1000

    match = re.findall(r'"shortTermInvestments":{"raw":(.*?),"fmt":"(.*?)","longFmt":"(.*?)"}', d)
    # 近四季短期投资
    if len(match) <= 3:
        short_invest_1 = 0
        short_invest_2 = 0
        short_invest_3 = 0
        short_invest_4 = 0
    else:
        short_invest_1 = float(match[0][0]) / 1000
        short_invest_2 = float(match[1][0]) / 1000
        short_invest_3 = float(match[2][0]) / 1000
        short_invest_4 = float(match[3][0]) / 1000
    # 预测等值现金
    cash_equal_1 = (cash_1 + short_invest_1)
    cash_equal_2 = (cash_2 + short_invest_2)
    cash_equal_3 = (cash_3 + short_invest_3)
    cash_equal_4 = (cash_4 + short_invest_4)
    # print(cash_equal_1, cash_equal_2, cash_equal_3, cash_equal_4)
    cash_equal = round(predict(cash_equal_1, cash_equal_2, cash_equal_3, cash_equal_4) / ex_ratio)

    match = re.findall(r'"totalCurrentAssets":{"raw":(.*?),"fmt":"(.*?)","longFmt":"(.*?)"}', d)
    # 预测目前资产
    assets_current_1 = float(match[0][0]) / 1000
    assets_current_2 = float(match[1][0]) / 1000
    assets_current_3 = float(match[2][0]) / 1000
    assets_current_4 = float(match[3][0]) / 1000
    # print(assets_current_1, assets_current_2, assets_current_3, assets_current_4)
    assets_current = round(predict(assets_current_1, assets_current_2, assets_current_3, assets_current_4) / ex_ratio)

    match = re.findall(r'"totalAssets":{"raw":(.*?),"fmt":"(.*?)","longFmt":"(.*?)"}', d)
    # 预测总资产
    assets_total_1 = float(match[0][0]) / 1000
    assets_total_2 = float(match[1][0]) / 1000
    assets_total_3 = float(match[2][0]) / 1000
    assets_total_4 = float(match[3][0]) / 1000
    # print(assets_total_1, assets_total_2, assets_total_3, assets_total_4)
    assets_total = round(predict(assets_total_1, assets_total_2, assets_total_3, assets_total_4) / ex_ratio)
    if beneish == 1:
        # 非流动资产
        noncurrent_asset_1 = assets_total_1 - assets_current_1
        noncurrent_asset_2 = assets_total_2 - assets_current_2

        # 资产质量指数
        AQI = (noncurrent_asset_1 / assets_total_1) / (noncurrent_asset_2 / assets_total_2)

    match = re.findall(r'"totalCurrentLiabilities":{"raw":(.*?),"fmt":"(.*?)","longFmt":"(.*?)"}', d)
    # 预测目前负债
    liab_current_1 = float(match[0][0]) / 1000
    liab_current_2 = float(match[1][0]) / 1000
    liab_current_3 = float(match[2][0]) / 1000
    liab_current_4 = float(match[3][0]) / 1000
    # print(liab_current_1, liab_current_2, liab_current_3, liab_current_4)
    liab_current = round(predict(liab_current_1, liab_current_2, liab_current_3, liab_current_4) / ex_ratio)

    match = re.findall(r'"totalLiab":{"raw":(.*?),"fmt":"(.*?)","longFmt":"(.*?)"}', d)
    # 预测总负债
    liab_total_1 = float(match[0][0]) / 1000
    liab_total_2 = float(match[1][0]) / 1000
    liab_total_3 = float(match[2][0]) / 1000
    liab_total_4 = float(match[3][0]) / 1000
    # print(liab_total_1, liab_total_2, liab_total_3, liab_total_4)
    liab_total = round(predict(liab_total_1, liab_total_2, liab_total_3, liab_total_4) / ex_ratio)

    if beneish == 1:
        # 财务杠杆指数
        LVGI = (liab_total_1 / assets_total_1) / (liab_total_2 / assets_total_2)

    match = re.findall(r'"totalStockholderEquity":{"raw":(.*?),"fmt":"(.*?)","longFmt":"(.*?)"}', d)
    # 预测股东权益总额
    equity_1 = float(match[0][0]) / 1000
    equity_2 = float(match[1][0]) / 1000
    equity_3 = float(match[2][0]) / 1000
    equity_4 = float(match[3][0]) / 1000
    # print(equity_1, equity_2, equity_3, equity_4)
    equity = round(predict(equity_1, equity_2, equity_3, equity_4) / ex_ratio)
    print('cash_equal:', cash_equal, 'assets_current:', assets_current, 'assets_total:', assets_total, 'liab_current:',
          liab_current, 'liab_total:', liab_total, 'equity:', equity)
    time.sleep(1)


    # cash_flow
    url = ('https://finance.yahoo.com/quote/' + stock_code + '/cash-flow?p=' + stock_code)
    firefox_options = Options()
    firefox_options.add_argument("--headless")  # define headless
    firefox_options.add_argument('--user-agent=%s' % user_agent)
    driver = webdriver.Firefox(options=firefox_options)  # 设置不打开网页,并伪装浏览器
    driver.get(url)  # 打开相应网页
    d = driver.page_source  # 获取网页html文件
    match = re.findall(r'Yahoo is part of (.*?) Media', d)
    # 判断是否有欢迎页面
    if match == ['Verizon']:
        driver.find_element_by_name("agree").click()
    driver.find_element_by_xpath("//div[@id='Col1-1-Financials-Proxy']/section/div/div[2]/button/div/span").click()
    time.sleep(timer)
    d = driver.page_source  # 获取网页html文件
    driver.close()
    match = re.findall(r'"totalCashFromOperatingActivities":{"raw":(.*?),"fmt":"(.*?)","longFmt":"(.*?)"}', d)
    # 营运现金流量
    cash_active_1 = float(match[-4][0]) / 1000
    cash_active_2 = float(match[-3][0]) / 1000
    cash_active_3 = float(match[-2][0]) / 1000
    cash_active_4 = float(match[-1][0]) / 1000
    cash_active = predict_sum(cash_active_1, cash_active_2, cash_active_3, cash_active_4) / ex_ratio

    if beneish == 1:
        # 应计系数
        TATA = (income_cops - cash_active) / assets_total

    match = re.findall(r'"capitalExpenditures":{"raw":(.*?),"fmt":"(.*?)","longFmt":"(.*?)"}', d)
    # 资本支出
    capital_ex_1 = float(match[-4][0]) / 1000
    capital_ex_2 = float(match[-3][0]) / 1000
    capital_ex_3 = float(match[-2][0]) / 1000
    capital_ex_4 = float(match[-1][0]) / 1000
    # 自由现金流量
    free_cash_flow_1 = round((cash_active_1 + capital_ex_1))
    free_cash_flow_2 = round((cash_active_2 + capital_ex_2))
    free_cash_flow_3 = round((cash_active_3 + capital_ex_3))
    free_cash_flow_4 = round((cash_active_4 + capital_ex_4))
    # 预测自由现金流量
    free_cash_flow = round(predict_sum(free_cash_flow_1,
                                       free_cash_flow_2, free_cash_flow_3, free_cash_flow_4) / ex_ratio)
    print('cash_active:', cash_active_1, cash_active_2, cash_active_3, cash_active_4, 'capital_extend:', capital_ex_1,
          capital_ex_2, capital_ex_3, capital_ex_4, 'free_cash_flow:', free_cash_flow)
    time.sleep(1)


    # analysis
    url = 'https://hk.finance.yahoo.com/quote/' + stock_code + '/analysis?p=' + stock_code
    r = session.get(url, headers=send_headers)
    # 预估eps
    eps_sel = 'table.BdB:nth-child(2) > tbody:nth-child(2) > tr:nth-child(2) > td:nth-child(4) > span:nth-child(1)'
    eps = float((r.html.find(eps_sel))[0].text.replace(',', ''))
    print('eps:', eps)
    growth_ratio_sel = 'table.W\(100\%\):nth-child(7) > tbody:nth-child(2) > tr:nth-child(3) > td:nth-child(2)'
    growth_ratio_first_sel = 'table.W\(100\%\):nth-child(7) > tbody:nth-child(2) > tr:nth-child(6) > td:nth-child(2)'
    growth_ratio_after_sel = 'table.W\(100\%\):nth-child(7) > tbody:nth-child(2) > tr:nth-child(5) > td:nth-child(2)'
    sp_500_sel = 'table.W\(100\%\):nth-child(7) > tbody:nth-child(2) > tr:nth-child(3) > td:nth-child(5)'
    if (r.html.find(growth_ratio_sel))[0].text == '無':
        growth_ratio_risk_adjustment_factor = 0
    else:
        growth_ratio_risk_adjustment_factor = round(float((r.html.find(growth_ratio_sel))[0].text.rstrip('%').replace(',', '')) / 1000, 4)
    if (r.html.find(growth_ratio_first_sel))[0].text == '無':
        growth_ratio_first = 0
    else:
        growth_ratio_first = round(float((r.html.find(growth_ratio_first_sel))[0].text.rstrip('%').replace(',', ''))
                                   / 100, 4)
    if (r.html.find(growth_ratio_after_sel))[0].text == '無':
        growth_ratio_after = 0
    else:
        growth_ratio_after = round(float((r.html.find(growth_ratio_after_sel))[0].text.rstrip('%').replace(',', ''))
                                   / 100, 4)
    if (r.html.find(sp_500_sel))[0].text == '無':
        sp_500 = 0
        print('未找到sp_500！')
    else:
        sp_500 = float((r.html.find(sp_500_sel))[0].text) / 100
    time.sleep(1)
    firefox_options = Options()
    firefox_options.add_argument("--headless")  # define headless
    firefox_options.add_argument('--user-agent=%s' % user_agent)
    driver = webdriver.Firefox(options=firefox_options)  # 设置不打开网页,并伪装浏览器
    driver.get(url)  # 打开相应网页
    d = driver.page_source  # 获取网页html文件
    match = re.findall(r'Yahoo is part of (.*?) Media', d)
    # 判断是否有欢迎页面
    if match == ['Verizon']:
        driver.find_element_by_name("agree").click()
    time.sleep(timer)
    d = driver.page_source  # 获取网页html文件
    driver.close()
    match = re.findall(r'"targetMeanPrice":{"raw":(.*?),"fmt":"(.*?)"}', d)
    analysis_price = float(match[0][0])
    print('growth_ratio_risk_adjustment_factor:', growth_ratio_risk_adjustment_factor, 'growth_ratio_first:', growth_ratio_first,
          'growth_ratio_after:', growth_ratio_after, 'sp_500:', sp_500, 'analysis_price:', analysis_price)
    time.sleep(1)


    if beneish == 1:
        # Beneish M-Score
        Beneish = -4.84 + 0.92 * DSRI + 0.528 * GMI + 0.404 * AQI + 0.892 * SGI + 0.115 * DEPI - 0.172 * SGAI + \
                  4.679 * TATA - 0.327 * LVGI
    else:
        Beneish = '无'
    print('Beneish:', Beneish)

    clock = get_timestamp()
    with open("Stocks.csv", "a",  newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([clock, stock_name, Beneish, price_current, beta, float_share_amount, roa, divi_yield, divi_payout,
                         total_revenue_1, total_revenue_2, total_revenue_3, total_revenue_4, total_earning_1,
                         total_earning_2, total_earning_3, total_earning_4, revenue, earning, rd_ratio, cash_equal,
                         assets_current, assets_total, liab_current, liab_total, equity, free_cash_flow, eps,
                         growth_ratio_risk_adjustment_factor, growth_ratio_first, growth_ratio_after, sp_500,
                         analysis_price, pe])
    # 设置消息提示框内容
    win32api.MessageBox(0, stock_name + '信息采集完成', "提醒", win32con.MB_ICONWARNING)
    sys.exit(0)
    return


if __name__ == '__main__':
    stock = 'ma'  # 股票代码
    stockname = 'mastercard'  # 股票名称
    Benei = 1  # Beneish查询开关
    pe_ra = 1  # pe-ratio查询开关
    exchange_ratio = 1  # 手动查询汇率 USD to Currency
    interval_time = 5  # 页面点击后间隔时长
    crawler(stock, stockname, interval_time, exchange_ratio, Benei, pe_ra)
