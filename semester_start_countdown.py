#!/usr/bin/env python
# coding: utf-8

# # The Claremont Colleges' Semester Start Timeline vs Los Angeles County COVID-19 Trends
# 
# ## Semester Start Dates
# * **Fall 2020** - 24 August 2020
# * **Spring 2021** - 25 January 2021
# 
# ## Last Update
# Monday, 2 November 2020
# 
# ## Data Sources
# * California Department of Public Health
#   * [COVID-19 Cases](https://data.ca.gov/dataset/covid-19-cases)
#   * [COVID-19 Hospital Data](https://data.ca.gov/dataset/covid-19-hospital-data)

# In[1]:


import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np
import pandas as pd
import requests
import seaborn as sns

sns.set()

LA_CASES_CSV = 'LA_County_Covid19_cases_deaths_date_table.csv'

CA_HOSPITALIZED_URL = 'https://data.ca.gov/dataset/529ac907-6ba1-4cb7-9aae-8966fc96aeef/resource/42d33765-20fd-44b8-a978-b083b7542225/download/hospitals_by_county.csv'
CA_HOSPITALIZED_CSV = 'ca_hospitalized.csv'

HTTP_OK = 200

COUNTY = 'county'
DATE = 'Date'
LOS_ANGELES = 'Los Angeles'
NEW_CASES_AVG = 'New Cases, 7 day average'
HOSPITALIZED_CONFIRMED_AVG = 'Hospitalized - Confrimed, 3 day average'
HOSPITALIZED_ALL_AVG = 'Hospitalized - Confirmed and Suspected, 3 day average'
SEMESTER = 'Semester'
DAYS_UNTIL_SEMESTER = 'Days Until Semester Start'

FALL_2020 = 'Fall 2020'
FALL_2020_START = pd.Timestamp('2020-08-24')
FALL_2020_COLOR = sns.color_palette()[0]
SPRING_2021 = 'Spring 2021'
SPRING_2021_START = pd.Timestamp('2021-01-25')
SPRING_2021_COLOR = sns.color_palette()[1]

X_AXIS_LABEL = 'Date (Fall 2020 timeline, Spring 2021 timeline)'

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

def date_axis_text(x, pos):
    td = pd.Timedelta(x, 'days')
    fall_equiv, spring_equiv = [
        (semester-td).strftime('%b %d') for semester in (FALL_2020_START, SPRING_2021_START)]
    return ('{}\n{}'.format(fall_equiv, spring_equiv))


# In[2]:


# Los Angeles County new cases table manually downloaded
fetch_ca_dataset(CA_HOSPITALIZED_URL, CA_HOSPITALIZED_CSV)


# In[4]:


la_cases = pd.read_csv(LA_CASES_CSV)
la_cases.rename(columns={'date_use': DATE, 'avg_cases': NEW_CASES_AVG}, inplace=True)
la_cases[DATE] = pd.to_datetime(la_cases[DATE])
lag_one_week, lag_two_week = [la_cases[DATE].max() - pd.Timedelta(x, 'days') for x in (7, 14)]
lag_one_y, lag_two_y = [
    la_cases.loc[la_cases[DATE]==x, NEW_CASES_AVG].iloc[0] for x in (lag_one_week, lag_two_week)]
lag_one_x, lag_two_x = [(SPRING_2021_START - x).days for x in (lag_one_week, lag_two_week)]

df_hospitalized = pd.read_csv(CA_HOSPITALIZED_CSV)
df_hospitalized.rename(columns={'todays_date': DATE}, inplace=True)
la_hospitalized = pd.DataFrame(df_hospitalized[df_hospitalized[COUNTY] == LOS_ANGELES])
la_hospitalized[DATE] = pd.to_datetime(la_hospitalized[DATE])

daily_average = (
    ('hospitalized_covid_confirmed_patients', HOSPITALIZED_CONFIRMED_AVG),
    ('hospitalized_covid_patients', HOSPITALIZED_ALL_AVG),
)
for col_day, col_avg in daily_average:
    la_hospitalized[col_avg] = la_hospitalized[col_day].rolling(3).mean().round(1)

df_la = pd.merge(la_cases, la_hospitalized, 'outer', DATE, sort=True)
df_la.reset_index(drop=True, inplace=True)
df_la = df_la.loc[:, (DATE, NEW_CASES_AVG, HOSPITALIZED_CONFIRMED_AVG, HOSPITALIZED_ALL_AVG)]

df_la[SEMESTER] = df_la[DATE].apply(lambda x: FALL_2020 if x <= FALL_2020_START else SPRING_2021)
df_la[DAYS_UNTIL_SEMESTER] = df_la.apply(days_until_start, 'columns')


# In[5]:


fig, ax = plt.subplots(figsize=(10, 5), dpi=300)

los_angeles_population = 9_651_332 * (10_257_557 / 10_269_935)
rate_multiplier = (los_angeles_population / 1e5) / 0.722
substantial_rate, moderate_rate = [rate_multiplier * x for x in (7, 4)]
widespread_color = '#802f67'
substantial_color = '#c43d53'
moderate_color = '#d97641'
widespread_message = 'Closed for in-person lectures'
substantial_message, moderate_message = [
    'Lecture capacity limited to {}%'.format(x) for x in (25, 50)]
vertical_pad = 50
horizontal_pad = 1
alpha = 0.75
ax.text(horizontal_pad, substantial_rate+50, widespread_message, ha='right', color=widespread_color, alpha=alpha)
ax.axhline(substantial_rate, color=substantial_color, linestyle='dashed', alpha=alpha)
ax.text(horizontal_pad, substantial_rate-vertical_pad, substantial_message,
        ha='right', va='top', color=substantial_color, alpha=alpha)
ax.axhline(moderate_rate, color=moderate_color, linestyle='dashed', alpha=alpha)
ax.text(horizontal_pad, moderate_rate-vertical_pad, moderate_message,
        ha='right', va='top', color=moderate_color, alpha=alpha)

ax.annotate('4th of July weekend\nreduced testing', xy=(49, 2275), xytext=(55, 1800),
           arrowprops={'arrowstyle':'->', 'color':'k'})

ax.set_title('Los Angeles County COVID-19 Transmission before TCC Semester')
ax.plot(DAYS_UNTIL_SEMESTER, NEW_CASES_AVG, color=FALL_2020_COLOR, label='Fall 2020',
        data=df_la[df_la[SEMESTER]==FALL_2020])

lag_tick_height = 30
ax.plot([lag_two_x]*2, [lag_two_y-lag_tick_height, lag_two_y+lag_tick_height],
       color=SPRING_2021_COLOR)
ax.plot([lag_one_x]*2, [lag_one_y-lag_tick_height, lag_one_y+lag_tick_height],
       color=SPRING_2021_COLOR)
ax.plot(DAYS_UNTIL_SEMESTER, NEW_CASES_AVG, color=SPRING_2021_COLOR, label='Spring 2021',
        data=df_la[(df_la[SEMESTER]==SPRING_2021) & (df_la[DATE]<=lag_two_week)])
ax.plot(DAYS_UNTIL_SEMESTER, NEW_CASES_AVG, linestyle='dashdot', color=SPRING_2021_COLOR,
        label='Spring 2021 (Reporting Lag)',
        data=df_la[(df_la[SEMESTER]==SPRING_2021) & (df_la[DATE]>=lag_two_week)])

ax.legend(title='Semester')
ax.set_xlabel(X_AXIS_LABEL)
ax.set_ylabel(NEW_CASES_AVG)
ax.set_xlim(120, 0)
ax.xaxis.set_major_formatter(FuncFormatter(date_axis_text))
ax.set_ylim(moderate_rate-vertical_pad-150, 3050)

# fig.savefig('docs/semester-start-v-new-cases.png')
fig.show()


# In[6]:


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
ax.set_xlabel(X_AXIS_LABEL)
ax.xaxis.set_major_formatter(FuncFormatter(date_axis_text))
ax.set_ylabel('Hospitalized, 3 day avgerage')
ax.set_title('Los Angeles County COVID-19 Hospital Patients before TCC Semester')
ax.set_xlim(120, 0)
ax.set_ylim(0)
# fig.savefig('docs/semester-start-v-hospitalized.png')
fig.show()


# In[ ]:




