position_total = 0
for i in position_amount:
    if type(i) is list:
        for j in i:
            if type(j) is int:
                position_total += j
    elif type(i) is int:
        position_total += i