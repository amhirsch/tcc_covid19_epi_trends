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


# In[ ]:


fetch_ca_dataset(CA_CASES_URL, CA_CASES_CSV)
fetch_ca_dataset(CA_HOSPITALIZED_URL, CA_HOSPITALIZED_CSV)


# In[ ]:


df_cases = pd.read_csv(CA_CASES_CSV)
la_cases = df_cases.loc[
    df_cases[COUNTY]==LOS_ANGELES].drop(columns=COUNTY).reset_index(drop=True)
la_cases.loc[:, DATE] = pd.to_datetime(la_cases.loc[:, DATE])

bad_data_id = 198
padding = 3
la_cases.loc[bad_data_id, NEW_CASES] = round(
    la_cases.loc[bad_data_id-padding:bad_data_id-1, NEW_CASES].append(
    la_cases.loc[bad_data_id+1:bad_data_id+padding, NEW_CASES]).mean())

la_cases.loc[201, NEW_CASES] = la_cases.loc[201, NEW_CASES] + 500
la_cases.loc[218, NEW_CASES] = la_cases.loc[218, NEW_CASES] - 500

la_cases.loc[214, NEW_CASES] = la_cases.loc[214, NEW_CASES] + 500
la_cases.loc[215, NEW_CASES] = la_cases.loc[215, NEW_CASES] + 500
la_cases.loc[216, NEW_CASES] = la_cases.loc[216, NEW_CASES] + 500
la_cases.loc[217, NEW_CASES] = la_cases.loc[217, NEW_CASES] + 500
la_cases.loc[218, NEW_CASES] = la_cases.loc[218, NEW_CASES] - 1000
la_cases.loc[219, NEW_CASES] = la_cases.loc[219, NEW_CASES] - 1000

la_cases.loc[221, NEW_CASES] = la_cases.loc[221, NEW_CASES] + 600
la_cases.loc[218, NEW_CASES] = la_cases.loc[218, NEW_CASES] - 600

la_cases.loc[222, NEW_CASES] = la_cases.loc[222, NEW_CASES] + 600
la_cases.loc[220, NEW_CASES] = la_cases.loc[220, NEW_CASES] - 600

# 1,500 new cases backlog reported on November 23
la_cases.loc[249, NEW_CASES] = la_cases.loc[249, NEW_CASES] + 1500
la_cases.loc[250, NEW_CASES] = la_cases.loc[250, NEW_CASES] - 1500

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


fig, ax = plt.subplots(figsize=(8, 5), dpi=300)

rate_multiplier = (10_257_557 / 1e5) / 0.642
substantial_rate, moderate_rate = [rate_multiplier * x for x in (7, 4)]
widespread_color = '#802f67'
substantial_color = '#c43d53'
moderate_color = '#d97641'
widespread_message = 'Closed for in-person lectures'
substantial_message, moderate_message = [
    'Lecture capacity limited to {}%'.format(x) for x in (25, 50)]
vertical_pad = 50
horizontal_pad = 1.5
alpha = 0.75
ax.text(horizontal_pad, substantial_rate+50, widespread_message, ha='right', color=widespread_color, alpha=alpha)
ax.axhline(substantial_rate, color=substantial_color, linestyle='dashed', alpha=alpha)
ax.text(horizontal_pad, substantial_rate-vertical_pad, substantial_message,
        ha='right', va='top', color=substantial_color, alpha=alpha)
# ax.axhline(moderate_rate, color=moderate_color, linestyle='dashed', alpha=alpha)
# ax.text(horizontal_pad, moderate_rate-vertical_pad, moderate_message,
#         ha='right', va='top', color=moderate_color, alpha=alpha)

ax.set_title('Los Angeles County COVID-19 Transmission before TCC Semester')
sns.lineplot(x=DAYS_UNTIL_SEMESTER, y=NEW_CASES_AVG, hue=SEMESTER, data=df_la, ax=ax)

ax.set_yticks(list(range(0, int(df_la[NEW_CASES_AVG].max())+500, 500)))
ax.set_yticklabels([f'{int(x):n}' if x%1e3==0 else '' for x in ax.get_yticks()])

ax.set_xlabel(X_AXIS_LABEL)
ax.set_ylabel(NEW_CASES_AVG)
ax.set_xlim(120, 0)
ax.xaxis.set_major_formatter(FuncFormatter(date_axis_text))
# ax.set_ylim(moderate_rate-vertical_pad-250, df_la[NEW_CASES_AVG].max()+100)
ax.set_ylim(600, df_la[NEW_CASES_AVG].max()+100)
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

ax.set_yticks(list(range(0, int(df_la[HOSPITALIZED_ALL_AVG].max()+500), 500)))
ax.set_yticklabels([f'{int(x):n}' if x%1e3==0 else '' for x in ax.get_yticks()])

ax.set_xlabel(X_AXIS_LABEL)
ax.xaxis.set_major_formatter(FuncFormatter(date_axis_text))
ax.set_ylabel('Hospitalized, 3 day avgerage')
ax.set_title('Los Angeles County COVID-19 Hospital Patients before TCC Semester')
ax.set_xlim(120, 0)
ax.set_ylim(-100, df_la[HOSPITALIZED_ALL_AVG].max()+100)

ax.legend(title='Semester, Patient COVID-19 Diagnosis', loc='lower right',
          ncol=2, fontsize='small', title_fontsize='small')

fig.savefig('docs/semester-start-v-hospitalized.png')
fig.show()


# In[ ]:




