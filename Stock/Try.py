import csv

with open("try.csv", "a", newline='') as csvfile:
    writer = csv.writer(csvfile)
    # 先写入columns_name
    writer.writerow(['date', 'name', 'price_current', 'beta', 'share_amount', 'roa', 'dividend_yield',
                     'dividend_payout', 'total_revenue_annual_1', 'total_revenue_annual_2',
                     'total_revenue_annual_3', 'total_revenue_annual_4', 'total_earning_annual_1',
                     'total_earning_annual_2', 'total_earning_annual_3', 'total_earning_annual_4',
                     'revenue', 'earning', 'R&D', 'cash_equal', 'assets_current', 'assets_total', 'liability_current',
                     'liability_total', 'equity', 'free_cash_flow', 'eps', 'growth_ratio_risk_adjustment_factor',
                     'growth_ratio_first', 'growth_ratio_after', 'sp_500_ratio', 'pe'])
