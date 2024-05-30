from pathlib import Path

import pandas as pd
from datetime import timedelta


# to be used with: https://github.com/klausj1/homeassistant-statistics

# Does not handle daylight savings time changes

if __name__ == '__main__':
    zaehler_csv = list(Path(__file__).parent.glob('ZAEHLERSTAENDE-*.csv'))
    if len(zaehler_csv) != 1:
        raise FileNotFoundError("Supply exactly 1 ZAEHLERSTAENDE csv file")
    viertel_csv = list(Path(__file__).parent.glob('VIERTELSTUNDENWERTE-*.csv'))
    if len(viertel_csv) != 1:
        raise FileNotFoundError("Supply exactly 1 VIERTELSTUNDENWERTE csv file")

    zaehler = pd.read_csv(zaehler_csv[0], sep=";", usecols=[0, 1], parse_dates=[0], decimal=",", names=["date", "value"], header=0, dayfirst=True).set_index("date")
    viertel = pd.read_csv(viertel_csv[0], sep=";", usecols=[0, 1, 3], parse_dates=[[0, 1]], decimal=",", names=["date", "time", "used"], header=0, dayfirst=True).set_index("date_time")
    viertel.index = viertel.index + timedelta(minutes=15)
    zaehler.index = zaehler.index + timedelta(days=1)
    viertel['value_calc'] = viertel.used.cumsum()
    diffs = zaehler.join(viertel)
    if len(diffs) != len(zaehler):
        raise ValueError("error in comparing the csv files")
    diffs = diffs.value - diffs.value_calc
    if diffs.max()-diffs.min() > 0.0001:
        raise ValueError("error in comparing the csv files")
    viertel.value_calc += diffs.median()
    result = (viertel.value_calc % 1000).to_frame().reset_index()
    result = result.loc[result.date_time.apply(lambda x: x.minute == 0)]
    result.date_time -= timedelta(hours=1)
    result = result.rename(columns={"date_time": "start", "value_calc": "state"})
    result['statistic_id'] = "sensor.energy"
    result['unit'] = "kWh"
    result['sum'] = result.state
    result = result[['statistic_id', 'unit', 'start', 'state', 'sum']]
    result = result.dropna()
    result.to_csv("output.csv", index=False, date_format="%d.%m.%Y %H:%M")
