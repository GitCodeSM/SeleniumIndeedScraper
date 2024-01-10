import pandas as pd

def to_numeric(x):
    for s in x.split():
        if s.isnumeric():
            return int(s)
        elif '+' in s:
            return int(s.rstrip('+'))
        else:
            return x

df_test = pd.read_csv("indeed_scraped_data.csv")

print(df_test.columns)

first = to_numeric('Active 4 days ago')
second = to_numeric('30+ days ago')
third = to_numeric('RECURRING_HIRE')

print(first)
print(second)
print(third)

df_test['formattedActivityDate'] = df_test.loc[df_test['formattedActivityDate'].notna(), 'formattedActivityDate'].apply(to_numeric) # correct
df_test['formattedActivityDate'].dropna()

df_test['formattedRelativeTime'] = df_test['formattedRelativeTime'].apply(to_numeric)
df_test['formattedRelativeTime'].dropna()

# df_test['hiresNeededExact'].dropna()
# df_test['hiresNeededExact'].values[1] # str
df_test['hiresNeededExact'] = df_test.loc[df_test['hiresNeededExact'].notna(), 'hiresNeededExact'].apply(to_numeric)
print(df_test['hiresNeededExact'].values) # perfect