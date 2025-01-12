import pandas as pd
import yfinance as yf
import quantstats as qs
from fredapi import Fred

# 設定 API Key
api_key = '8ab5c621a48fd00a1360158a99f0848b'
fred = Fred(api_key=api_key)
data1 = fred.get_series('DBAA')
data2 = fred.get_series('DGS10')  # Moody's Seasoned Baa Corporate Bond Yield # 美國十年期公債殖利率
rolling_years = 10

tmp = (data1-data2).dropna().ewm(span = 252*rolling_years, min_periods = 252*rolling_years ).mean() #span: rolling days
df = pd.DataFrame((data1-data2), columns=['HYS'])
df['10year_EMA'] = tmp
df = df.shift(2) # For delayed data

'''Peaks and troughs'''
month = 90
peak = df['HYS'].min()
peaks = []
l_peak = []
l_peaks = 0
trough = df['HYS'].max()
troughs = []
for _,row in df.iterrows():
    if row['HYS'] > row['10year_EMA'] and row['HYS'] > peak:
        peak = row['HYS']
        thorugh = df['HYS'].max()
        peaks.append(peak)
        troughs.append(trough)
    elif row['HYS'] < row['10year_EMA'] and row['HYS'] < trough:
        peak = df['HYS'].min()
        trough = row['HYS']
        peaks.append(peak)
        troughs.append(trough)
    else:
        peaks.append(peak)
        troughs.append(trough)

df['peak'] = peaks
df['trough'] = troughs
df['slope'] = df['HYS'].pct_change(month)
df = df.dropna()

conditions = []
condition = 0
targets = []
target = 0

for _,row in df.iterrows():
    if   row['HYS'] > row['10year_EMA'] and row['slope'] > 0:
        condition = 1
        target = ['XLP']
    elif row['HYS'] > row['10year_EMA'] and row['slope'] < 0:
        condition = 2
        target = ['XLY','XLB']
    elif row['HYS'] < row['10year_EMA'] and row['slope'] > 0:
        condition = 3
        target = ['XLF','XLE','XLI']
    elif row['HYS'] < row['10year_EMA'] and row['slope'] < 0:
        condition = 4
        target = ['XLK','XLV']
   
    else:
        condition = condition
        target = target

    conditions.append(condition)
    targets.append(target)

df['condition'] = conditions
df['targets'] = targets

# Backtesting
universe_= ['XLE','XLF','XLK','XLV','XLI','XLY','XLP','XLU','XLB']
df_price = yf.download(universe_)
df_return = df_price['Adj Close'].pct_change().dropna()

db = pd.DataFrame(columns = df_return.columns, index = df.index)
weight = 0
for _,row in df.iterrows():
    targets = row['targets']
    weight = 1/len(row['targets']) 
    for col in targets:
        db[col][row.name] = weight 
db = db.shift(1).fillna(0) #shift one day for original

db.to_csv('Sotos_sector_rotation.csv')
