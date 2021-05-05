import pandas as pd
import folium
import altair as alt

import app_data

df = app_data.load()

chain_sel = df.Customer.str.startswith('Kroger') | df.Customer.str.startswith('HEB')
chain_df = df[chain_sel]

chain_list = chain_df.drop_duplicates('Customer').loc[:,['Customer', 'Address']]
chain_list['Address'] = chain_list.Address.str.strip().str.replace("\n",", ")

chain_list = app_data.get_locations(chain_list)

