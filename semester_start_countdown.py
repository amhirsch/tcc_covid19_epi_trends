#!/usr/bin/env python
# coding: utf-8

# # The Claremont Colleges' Semester Start Timeline vs Los Angeles County COVID-19 Trends
# 
# ## Semester Start Dates
# * **Fall 2020** - 24 August 2020
# * **Spring 2021** - 25 January 2021
# 
# <!--## Last Update
# Tuesday, 3 November 2020 -->
# 
# ## Data Sources
# * California Department of Public Health
#   * [COVID-19 Cases](https://data.ca.gov/dataset/covid-19-cases/resource/926fd08f-cc91-4828-af38-bd45de97f8c3?filters=county%3ALos+Angeles)
#   * [COVID-19 Hospital Data](https://data.ca.gov/dataset/covid-19-hospital-data/resource/42d33765-20fd-44b8-a978-b083b7542225?filters=county%3ALos+Angeles)

# In[ ]:


import locale
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np
import pandas as pd
import requests
import seaborn as sns

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

plt.rcParams.update({'figure.autolayout': True})
sns.set()

CA_CASES_URL = 'https://data.ca.gov/dataset/590188d5-8545-4c93-a9a0-e230f0db7290/resource/926fd08f-cc91-4828-af38-bd45de97f8c3/download/statewide_cases.csv'
CA_CASES_CSV = 'ca_cases.csv'

CA_HOSPITALIZED_URL = 'https://data.ca.gov/dataset/529ac907-6ba1-4cb7-9aae-8966fc96aeef/resource/42d33765-20fd-44b8-a978-b083b7542225/download/hospitals_by_county.csv'
CA_HOSPITALIZED_CSV = 'ca_hospitalized.csv'

COUNTY = 'county'
DATE = 'date'
NEW_CASES = 'newcountconfirmed'
LOS_ANGELES = 'Los Angeles'
NEW_CASES_AVG = 'New Cases, 14 day average'
HOSPITALIZED_CONFIRMED_AVG = 'Hospitalized - Confrimed, 3 day average'
HOSPITALIZED_ALL_AVG = 'Hospitalized - Confirmed and Suspected, 3 day average'
SEMESTER = 'Semester'
DAYS_UNTIL_SEMESTER = 'Days Until Semester Start'

CASE_ROLLING_WINDOW = 14
NEW_CASES_AVG = 'New Cases, {} day average'.format(CASE_ROLLING_WINDOW)

FALL_2020 = 'Fall 2020'
FALL_2020_START = pd.Timestamp('2020-08-24')
FALL_2020_COLOR = sns.color_palette()[0]
SPRING_2021 = 'Spring 2021'
SPRING_2021_START = pd.Timestamp('2021-01-25')
SPRING_2021_COLOR = sns.color_palette()[1]

X_AXIS_LABEL = 'Date (Fall 2020 timeline, Spring 2021 timeline)'

def fetch_ca_dataset(url, output_csv):
    r = requests.get(url)
    if r.status_code == 200:
        with open(output_csv, 'w') as f:
            f.write(r.text)
    else:
        raise ConnectionError('HTTP code not 200')

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

def chart_upper_bound(dep_var_series, tick_step, buffer):
    ticks_needed = (dep_var_series.max() + tick_step) // tick_step
    return int(tick_step * ticks_needed + buffer)

def chart_lower_bound(upper_bound, ratio, top_value):
    return (ratio * upper_bound - top_value) / (ratio - 1)


# In[ ]:


fetch_ca_dataset(CA_CASES_URL, CA_CASES_CSV)
fetch_ca_dataset(CA_HOSPITALIZED_URL, CA_HOSPITALIZED_CSV)


# In[ ]:


df_cases = pd.read_csv(CA_CASES_CSV)
la_cases = df_cases.loc[
    df_cases[COUNTY]==LOS_ANGELES
].drop(columns=COUNTY).reset_index(drop=True).copy()
la_cases[DATE] = pd.to_datetime(la_cases[DATE])

# Forward fill new cases for negative new cases day.
la_cases.loc[198, NEW_CASES] = pd.NA
la_cases[NEW_CASES].ffill(inplace=True)

la_cases[NEW_CASES_AVG] = la_cases.loc[:, NEW_CASES].rolling(CASE_ROLLING_WINDOW).mean()

df_hospitalized = pd.read_csv(CA_HOSPITALIZED_CSV).rename(columns={'todays_date': DATE})
la_hospitalized = df_hospitalized.loc[
    df_hospitalized[COUNTY]==LOS_ANGELES].drop(columns=COUNTY).reset_index(drop=True)
la_hospitalized.loc[:, DATE] = pd.to_datetime(la_hospitalized.loc[:, DATE])

daily_average = (
    ('hospitalized_covid_confirmed_patients', HOSPITALIZED_CONFIRMED_AVG),
    ('hospitalized_covid_patients', HOSPITALIZED_ALL_AVG),
)
for col_day, col_avg in daily_average:
    la_hospitalized[col_avg] = la_hospitalized[col_day].rolling(3).mean().round(1)

df_la = pd.merge(la_cases, la_hospitalized, on=DATE).reset_index(drop=True)
df_la[SEMESTER] = df_la.loc[:, DATE].apply(
    lambda x: FALL_2020 if x <= FALL_2020_START else SPRING_2021)
df_la[DAYS_UNTIL_SEMESTER] = df_la.apply(days_until_start, 'columns')
df_la = df_la.loc[:, (DATE, SEMESTER, DAYS_UNTIL_SEMESTER,
                      NEW_CASES_AVG, HOSPITALIZED_CONFIRMED_AVG, HOSPITALIZED_ALL_AVG)]


# In[ ]:


fig, ax = plt.subplots(figsize=(8, 5.5), dpi=300)

rate_multiplier = (10_257_557 / 1e5) / 0.500
substantial_rate, moderate_rate = [rate_multiplier * x for x in (7, 4)]
widespread_color = '#802f67'
substantial_color = '#c43d53'
moderate_color = '#d97641'
widespread_message = 'Closed for in-person lectures'
substantial_message, moderate_message = [
    'Lecture capacity limited to {}%'.format(x) for x in (25, 50)]
vertical_pad = 100
horizontal_pad = 5
alpha = 0.75
ax.text(horizontal_pad, substantial_rate+vertical_pad, widespread_message,
        ha='right', color=widespread_color, alpha=alpha)
ax.axhline(substantial_rate, color=substantial_color, linestyle='dashed', alpha=alpha)
ax.text(horizontal_pad, substantial_rate-vertical_pad, substantial_message,
        ha='right', va='top', color=substantial_color, alpha=alpha)
# ax.axhline(moderate_rate, color=moderate_color, linestyle='dashed', alpha=alpha)
# ax.text(horizontal_pad, moderate_rate-vertical_pad, moderate_message,
#         ha='right', va='top', color=moderate_color, alpha=alpha)

ax.set_title('Los Angeles County COVID-19 Transmission before TCC Semester')
sns.lineplot(x=DAYS_UNTIL_SEMESTER, y=NEW_CASES_AVG, hue=SEMESTER, data=df_la, ax=ax)

tick_step = 1500
y_max = chart_upper_bound(df_la[NEW_CASES_AVG], tick_step, 200)
ax.set_yticks(list(range(0, y_max, tick_step)))
ax.set_yticklabels([f'{int(x):n}' if x%3_000==0 else '' for x in ax.get_yticks()])

ax.set_xlabel(X_AXIS_LABEL)
ax.set_ylabel(NEW_CASES_AVG)
ax.set_xlim(120, 0)
ax.xaxis.set_major_formatter(FuncFormatter(date_axis_text))
# ax.set_ylim(moderate_rate-vertical_pad-250, df_la[NEW_CASES_AVG].max()+100)
ax.set_ylim(0, y_max)
ax.legend(loc='upper left', title=SEMESTER)

fig.savefig('docs/semester-start-v-new-cases.png')
fig.show()


# In[ ]:


fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
ax.plot(DAYS_UNTIL_SEMESTER, HOSPITALIZED_ALL_AVG, 'b--', label='Fall 2020, Confirmed & Suspected',
        data=df_la[df_la[SEMESTER] == FALL_2020])
ax.plot(DAYS_UNTIL_SEMESTER, HOSPITALIZED_CONFIRMED_AVG, 'b-', label='Fall 2020, Confirmed',
        data=df_la[df_la[SEMESTER] == FALL_2020])
ax.plot(DAYS_UNTIL_SEMESTER, HOSPITALIZED_ALL_AVG, '--', color=sns.color_palette()[1],
        label='Spring 2021, Confirmed & Suspected', data=df_la[df_la[SEMESTER] == SPRING_2021])
ax.plot(DAYS_UNTIL_SEMESTER, HOSPITALIZED_CONFIRMED_AVG, color=sns.color_palette()[1], label='Spring 2021, Confirmed',
        data=df_la[df_la[SEMESTER] == SPRING_2021])

tick_step = 1000
y_max = chart_upper_bound(df_la[HOSPITALIZED_ALL_AVG], tick_step, 200)
ax.set_yticks(list(range(0, y_max, tick_step)))
ax.set_yticklabels([f'{int(x):n}' if x%2_000==0 else '' for x in ax.get_yticks()])

ax.set_xlabel(X_AXIS_LABEL)
ax.xaxis.set_major_formatter(FuncFormatter(date_axis_text))
ax.set_ylabel('Hospitalized, 3 day avgerage')
ax.set_title('Los Angeles County COVID-19 Hospital Patients before TCC Semester')
ax.set_xlim(120, 0)

legend_top = 600
# ax.axhline(legend_top, color='k')
ax.set_ylim(chart_lower_bound(y_max, .2, legend_top), y_max)

ax.legend(title='Semester, Patient COVID-19 Diagnosis', loc='lower right',
          ncol=2, fontsize='small', title_fontsize='small')

fig.savefig('docs/semester-start-v-hospitalized.png')
fig.show()


# In[ ]:


LACDPH_CSV = 'lacdph.csv'
r = requests.get('https://github.com/amhirsch/lac_covid19/raw/master/docs/time-series/aggregate-ts.csv')
if r.status_code == 200:
    with open(LACDPH_CSV, 'w') as f:
        f.write(r.text)
else:
    raise ConnectionError('LACDPH Time Series Unavailable')


# In[ ]:


df_lacdph = pd.read_csv(LACDPH_CSV)
df_lacdph[DATE] = pd.to_datetime(df_lacdph['Date'])
df_lacdph = df_lacdph.loc[df_lacdph[DATE]>=pd.to_datetime('2020-12-01'),
                          [DATE, 'New cases']].copy().reset_index(drop=True)
df_lacdph[NEW_CASES_AVG] = df_lacdph['New cases'].rolling(14).mean()


# In[ ]:


reopening_threshold = 10 / 100_000 * 10_260_237
fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
sns.lineplot(x=DATE, y=NEW_CASES_AVG, data=df_lacdph, ax=ax)
ax.axhline(reopening_threshold, linestyle='dashed', color='k')
ax.text(pd.to_datetime('2021-01-02'), reopening_threshold+300, 'LACDPH Reopening Waivers')

ax.set_xlim(pd.to_datetime('2021-01-01'), pd.to_datetime('2021-03-12'))
ax.set_ylim(0)
ax.tick_params('x', labelrotation=90)

fig.show()


# In[ ]:




