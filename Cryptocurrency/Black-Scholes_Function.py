import os
import datetime
import numpy as np
from scipy.stats import norm
import ex.swap_api as swap
import ex.spot_api as spot


def Black_Scholes_Function(S, K, T, r, sigma, option):
    """
    S: spot price
    K: strike price
    T: time to maturity
    r: risk-free interest rate
    sigma: standard deviation of price of underlying asset
    """
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = (np.log(S / K) + (r - 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))

    if option == 'call':
        p = (S * norm.cdf(d1, 0.0, 1.0) - K * np.exp(-r * T) * norm.cdf(d2, 0.0, 1.0))
    elif option == 'put':
        p = (K * np.exp(-r * T) * norm.cdf(-d2, 0.0, 1.0) - S * norm.cdf(-d1, 0.0, 1.0))
    else:
        return None
    return p


def Run():
    # Set Up Global Proxy
    os.environ['http_proxy'] = 'http://127.0.0.1:1711'
    os.environ['https_proxy'] = 'https://127.0.0.1:1711'
    swapAPI = swap.SwapAPI(api_key, secret_key, passphrase, False)
    spotAPI = spot.SpotAPI(api_key, secret_key, passphrase, False)

    coin = 'BTC'  # Underlying
    # Parameters
    direction = 'call'
    Expiration_Time = datetime.datetime.strptime('2021-03-26 16:00:00', '%Y-%m-%d %H:%M:%S')
    Exercise_Price = 72000
    Implied_Volatility = 88.91

    coin_swap = coin + '-USD-SWAP'
    coin_spot = coin + '-USDT'
    Implied_Volatility = Implied_Volatility / 100
    # Crypto_Price
    Crypto_Price = spotAPI.get_specific_ticker(coin_spot)
    best_ask = float(Crypto_Price['best_ask'])
    best_bid = float(Crypto_Price['best_bid'])
    Crypto_Price = (best_ask + best_bid) / 2
    # Maturity_Time
    Time_Now = datetime.datetime.strptime(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
    Maturity_Time = float((Expiration_Time - Time_Now).total_seconds())
    Year_Time = 31536000
    Maturity_Time = Maturity_Time / Year_Time
    # Risk_Free_Interest_Rate
    Risk_Free_Interest_Rate = float(swapAPI.get_funding_time(coin_swap)['funding_rate'])

    # B-S Function Calculation
    Dollars = Black_Scholes_Function(Exercise_Price, Crypto_Price, Maturity_Time, Risk_Free_Interest_Rate,
                                     Implied_Volatility, direction)
    BTC = Dollars / Crypto_Price
    print(Dollars, '$ ', BTC, 'Coin')


if __name__ == '__main__':
    # Watch_Only
    api_key = ""
    secret_key = ""
    passphrase = ""
    Run()
