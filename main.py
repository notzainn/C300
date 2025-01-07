import pandas as pd
rating = pd.read_csv('Cleansed Set B Corporate Rating.csv')

df_loaded = pd.read_pickle('df.pkl')
print(df_loaded)