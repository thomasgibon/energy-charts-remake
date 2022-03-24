import pandas as pd
from datetime import datetime
import requests
import json
import matplotlib.pyplot as plt
from ast import literal_eval as make_tuple
import numpy as np
import seaborn as sns

def get_trade(country='de',
              year='2021',
              lang='en',
              display=False):
    
    s = requests.Session()
    
    url = f'https://energy-charts.info/charts/power/data/{country}/year_cbpf_saldo_{year}.json'
    
    r = s.get(url)
    
    s.close()
    
    if r.status_code == 404:
        print('File not found!')
        return None, None
    
    response = json.loads(r.text)
    
    ticks = [datetime.utcfromtimestamp(d/1000) for d in response[0]['xAxisValues']]
    
    trade = []
    regions = []

    for r in response:
        trade.append(r['data'])
        regions.append(r['name'][0][lang])
        
    colors = {t:tuple(c/255 for c in make_tuple(r['color'][3:])) for r,t in zip(response,regions)}
    colors = {**colors, **{'_'+k:v for k,v in colors.items()}}
    
    print(url)
    
    trade_df = pd.DataFrame(data=trade,
                      index=regions,
                      columns=ticks).T
    
    if display:
        df_neg, df_pos = trade_df.drop('sum',axis=1).clip(upper=0), trade_df.drop('sum',axis=1).clip(lower=0)

        fig, ax = plt.subplots(figsize=(20,5),
                               facecolor='w')

        df_pos.plot.area(stacked=True,
                         linewidth=0.,
                         color=colors,
                         ax=ax)

        df_neg.rename(columns=lambda x: '_' + x, inplace=True)

        df_neg.plot.area(ax=ax,
                        stacked=True,
                        linewidth=0.,
                        color=colors)

        # handles, labels = ax.get_legend_handles_labels()

        # plt.legend(handles=handles,
        #            loc='center left',
        #            bbox_to_anchor=(1, 0.5))

        ax.set_ylim([df_neg.sum(axis=1).min()*1.1,
                     df_pos.sum(axis=1).max()*1.1])
        
    return trade_df, colors

def get_prod(country='de',
              step='day',
              year='2021',
              lang='en',
              load=True,
              display=True,
              cumul=False,
              rolling=False):
    
    s = requests.Session()
    
#     if not (country == 'de' and int(year) < 2019):
        
    url = f'https://energy-charts.info/charts/energy/data/{country}/{step}_{year}.json'

    if step == 'hour':
        url = f'https://energy-charts.info/charts/power/data/{country}/year_{year}.json'

    r = s.get(url)

    s.close()
    
    if r.status_code == 404:
        print('File not found!')
        return None, None, None
    
    response = json.loads(r.text)

    try:
        techs = [r['name'][0][lang] for r in response]
    except KeyError:
        techs = [r['name'][lang] for r in response]

    prod  = [r['data'] for r in response]

    if step != 'hour':
        ticks = [datetime.strptime(d, '%d.%m.%Y') for d in response[0]['xAxisValues']]
    else:
        ticks = [pd.to_datetime(d, unit='ms', origin='unix') for d in response[0]['xAxisValues']]

    colors = {t:tuple(c/255 for c in make_tuple(r['color'][3:])) for r,t in zip(response,techs)}
    colors = {**colors, **{'_'+k:v for k,v in colors.items()}}
    load_dict = {'en': 'Load', 'de': 'Last', 'fr': 'Charge', 'it': 'Carico'}
        
#     else:
        
#         url = f'https://energy-charts.info/charts/energy/raw_data/{country}/{step}_{year}.json'
        
#         r = s.get(url)
    
#         s.close()
    
#         response = json.loads(r.text)
        
#         techs = [r['key'][0][lang] for r in response]
#         prod  = [[v[1] for v in r['values']] for r in response]
#         ticks = [[datetime.strptime(v[0], '%d.%m.%Y') for v in r['values']] for r in response][0]
        
#         colors = {t:tuple(c/255 for c in make_tuple(r['color'][3:])) for r,t in zip(response,techs)}
#         colors = {**colors, **{'_'+k:v for k,v in colors.items()}}
#         load_dict = {'en': 'Load', 'de': 'Last', 'fr': 'Charge', 'it': 'Carico'}
        
    print(url)

    prod_df = pd.DataFrame(data=prod,
                      index=techs,
                      columns=ticks).T
    
    col_exclude = ['Residual load', 'Renewable Share']
    
    for col in col_exclude:
        if col in prod_df.columns:
            prod_df.drop(col,axis=1,inplace=True)
    
    if rolling:
        prod_df = prod_df.rolling(rolling).sum()
    
    if cumul:
        prod_df = prod_df.cumsum()
        
    load_df = prod_df[load_dict[lang]]
    prod_df.drop(load_dict[lang], axis=1, inplace=True)
    
    if display:
        fig, ax = plt.subplots(figsize=(20,10), facecolor='w')
        # split dataframe df into negative only and positive only values
        df_neg, df_pos = prod_df.clip(upper=0), prod_df.clip(lower=0)
        # stacked area plot of positive values
        prod_plt = df_pos.plot.area(ax=ax,
                         stacked=True,
                         linewidth=0.,
                         color=colors)
        # stacked area plot of negative values, prepend column names with '_' such that they don't appear in the legend
        df_neg.rename(columns=lambda x: '_' + x).plot.area(ax=ax, stacked=True, linewidth=0., color=colors)

        if load:
            load_plt = load_df.plot(ax=ax,
                         linewidth=2,
                         color=colors[load_dict[lang]])
            
        handles, labels = ax.get_legend_handles_labels()

        plt.legend(handles=handles,
                   loc='center left',
                   bbox_to_anchor=(1, 0.5))

        # rescale the y axis
        ax.set_ylim([df_neg.sum(axis=1).min()*1.1, df_pos.sum(axis=1).max()*1.1])
        
        
    return prod_df, load_df, colors