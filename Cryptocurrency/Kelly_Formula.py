def Kelly_formula(p, b):
    Proportion = ((p / 100) * (b + 1) - 1) / b
    return Proportion


win_rate = 60
exercise_price = 60000
pre_exercise_price = 70000
price = 7700
if pre_exercise_price > exercise_price:
    odds = (pre_exercise_price - exercise_price) / price
else:
    odds = (exercise_price - pre_exercise_price) / price
P = Kelly_formula(win_rate, odds)
print('Win_to_Loss_Ratio:', odds, '\n', 'Bets_Ratio:', P)
