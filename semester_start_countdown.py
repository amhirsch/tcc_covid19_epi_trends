#!/usr/bin/env python
# coding: utf-8

# # The Claremont Colleges' Semester Start Timeline vs Los Angeles County COVID-19 Trends
# 
# ## Semester Start Dates
# * **Fall 2020** - 24 August 2020
# * **Spring 2021** - 19 January 2021
# 
# ## Last Update
# Sunday, 18 October 2020
# 
# ## Data Sources
# * California Department of Public Health
#   * [COVID-19 Cases](https://data.ca.gov/dataset/covid-19-cases)
#   * [COVID-19 Hospital Data](https://data.ca.gov/dataset/covid-19-hospital-data)

# In[1]:


import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import seaborn as sns

sns.set()

CA_CASES_URL = 'https://data.ca.gov/dataset/590188d5-8545-4c93-a9a0-e230f0db7290/resource/926fd08f-cc91-4828-af38-bd45de97f8c3/download/statewide_cases.csv'
CA_CASES_CSV = 'ca_cases.csv'

CA_HOSPITALIZED_URL = 'https://data.ca.gov/dataset/529ac907-6ba1-4cb7-9aae-8966fc96aeef/resource/42d33765-20fd-44b8-a978-b083b7542225/download/hospitals_by_county.csv'
CA_HOSPITALIZED_CSV = 'ca_hospitalized.csv'

HTTP_OK = 200

COUNTY = 'county'
DATE = 'date'
LOS_ANGELES = 'Los Angeles'
NEW_CASES = 'newcountconfirmed'
NEW_CASES_AVG = 'New Cases, 7 day average'
HOSPITALIZED_CONFIRMED = 'hospitalized_covid_confirmed_patients'
HOSPITALIZED_CONFIRMED_AVG = 'Hospitalized - Confrimed, 3 day average'
HOSPITALIZED_ALL = 'hospitalized_covid_patients'
HOSPITALIZED_ALL_AVG = 'Hospitalized - Confirmed and Suspected, 3 day average'
SEMESTER = 'Semester'
DAYS_UNTIL_SEMESTER = 'Days Until Semester Start'


FALL_2020 = 'Fall 2020'
FALL_2020_START = pd.Timestamp('2020-08-24')
SPRING_2021 = 'Spring 2021'
SPRING_2021_START = pd.Timestamp('2021-01-19')

def fetch_ca_dataset(url, output_csv):
    r = requests.get(url)
    if r.status_code == HTTP_OK:
        with open(output_csv, 'w') as f:
            f.write(r.text)

def days_until_start(row: pd.Series) -> int:
    if row[SEMESTER] == FALL_2020:
        return (FALL_2020_START - row[DATE]).days
    elif row[SEMESTER] == SPRING_2021:
        return (SPRING_2021_START - row[DATE]).days


# In[2]:


fetch_ca_dataset(CA_CASES_URL, CA_CASES_CSV)
fetch_ca_dataset(CA_HOSPITALIZED_URL, CA_HOSPITALIZED_CSV)


# In[3]:


df_cases = pd.read_csv(CA_CASES_CSV)
df_hospitalized = pd.read_csv(CA_HOSPITALIZED_CSV)
la_cases = df_cases[df_cases[COUNTY] == LOS_ANGELES]
la_hospitalized = df_hospitalized[df_hospitalized[COUNTY] == LOS_ANGELES]

df_la = pd.merge(la_cases, la_hospitalized, left_on=DATE, right_on='todays_date')
df_la.reset_index(drop=True, inplace=True)
df_la = df_la.loc[:, (DATE, NEW_CASES, HOSPITALIZED_CONFIRMED, HOSPITALIZED_ALL)]

# Approximate the new cases for October 2, 2020 as
# the mean of new cases three days before and after
bad_data_id = 187
padding = 3
df_la.loc[bad_data_id, NEW_CASES] = round(
    df_la.loc[bad_data_id-padding:bad_data_id-1, NEW_CASES].append(
    df_la.loc[bad_data_id+1:bad_data_id+padding, NEW_CASES]).mean())

df_la.loc[:, (DATE,)] = pd.to_datetime(df_la[DATE])
df_la.loc[:, (HOSPITALIZED_CONFIRMED,)] = df_la[HOSPITALIZED_CONFIRMED].astype('int')

daily_average = (
    (NEW_CASES, NEW_CASES_AVG, 7),
    (HOSPITALIZED_CONFIRMED, HOSPITALIZED_CONFIRMED_AVG, 3),
    (HOSPITALIZED_ALL, HOSPITALIZED_ALL_AVG, 3),
)
for col_day, col_avg, window in daily_average:
    df_la[col_avg] = df_la[col_day].rolling(window).mean().round(1)

df_la[SEMESTER] = df_la[DATE].apply(lambda x: FALL_2020 if x <= FALL_2020_START else SPRING_2021)
df_la[DAYS_UNTIL_SEMESTER] = df_la.apply(days_until_start, 'columns')


# In[4]:


fig, ax = plt.subplots(figsize=(10, 4), dpi=300)
ax.set_title("Los Angeles County COVID-19 Transmission before TCC Semester")
sns.lineplot(DAYS_UNTIL_SEMESTER, NEW_CASES_AVG, SEMESTER, data=df_la, ax=ax)
ax.set_xlim(120, 0)
ax.set_ylim(500)
# fig.savefig('docs/semester-start-v-new-cases.png')
fig.show()


# In[5]:


fig, ax = plt.subplots(figsize=(10, 4), dpi=300)
ax.plot(DAYS_UNTIL_SEMESTER, HOSPITALIZED_ALL_AVG, 'b--', label='Fall 2020, Confirmed and Suspected',
        data=df_la[df_la[SEMESTER] == FALL_2020])
ax.plot(DAYS_UNTIL_SEMESTER, HOSPITALIZED_CONFIRMED_AVG, 'b-', label='Fall 2020, Confirmed',
        data=df_la[df_la[SEMESTER] == FALL_2020])
ax.plot(DAYS_UNTIL_SEMESTER, HOSPITALIZED_ALL_AVG, '--', color=sns.color_palette()[1],
        label='Spring 2021, Confirmed and Suspected', data=df_la[df_la[SEMESTER] == SPRING_2021])
ax.plot(DAYS_UNTIL_SEMESTER, HOSPITALIZED_CONFIRMED_AVG, color=sns.color_palette()[1], label='Spring 2021, Confirmed',
        data=df_la[df_la[SEMESTER] == SPRING_2021])

ax.legend(title='Semester, Patient COVID-19 Diagnosis')
ax.set_xlabel(DAYS_UNTIL_SEMESTER)
ax.set_ylabel('Hospitalized, 3 day avgerage')
ax.set_title("Los Angeles County COVID-19 Hospital Patients before TCC Semester")
ax.set_xlim(120, 0)
ax.set_ylim(0)
# fig.savefig('docs/semester-start-v-hospitalized.png')
fig.show()


# In[ ]:




