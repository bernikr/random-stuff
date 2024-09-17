from pathlib import Path

import pandas as pd
from datetime import timedelta


# to be used with: https://github.com/klausj1/homeassistant-statistics
# IMPORTANT: Output tz is UTC

if __name__ == '__main__':
    zaehler_csv = list(Path(__file__).parent.glob('ZAEHLERSTAENDE-*.csv'))
    if len(zaehler_csv) != 1:
        raise FileNotFoundError("Supply exactly 1 ZAEHLERSTAENDE csv file")
    viertel_csv = list(Path(__file__).parent.glob('VIERTELSTUNDENWERTE_ECONTROL-*.csv'))
    if len(viertel_csv) != 1:
        raise FileNotFoundError("Supply exactly 1 VIERTELSTUNDENWERTE_ECONTROL csv file")

    zaehler = pd.read_csv(zaehler_csv[0], sep=";", usecols=[0, 1], parse_dates=[0], decimal=",", names=["date", "value"], header=0, dayfirst=True).dropna().set_index("date")
    viertel = pd.read_csv(viertel_csv[0], sep=";", usecols=[0, 3], parse_dates=[0], decimal=",", names=["date_time", "used"], header=0).dropna().set_index("date_time")
    zaehler.index = (zaehler.index + timedelta(days=1)).tz_localize('Europe/Vienna').tz_convert("UTC")
    viertel.index = pd.to_datetime(viertel.index, utc=True)
    viertel.loc[viertel.index[0] - timedelta(minutes=15)] = 0
    viertel = viertel.sort_index()
    viertel['value_calc'] = viertel.used.cumsum()
    diffs = zaehler.join(viertel, how="inner")
    #if sum(viertel.index.map(lambda x: x.minute == 0 and x.tz_convert('Europe/Vienna').hour == 0)) != len(diffs):
    #    raise ValueError("error in comparing the csv files: not the same days")
    diffs = diffs.value - diffs.value_calc
    if diffs.max()-diffs.min() > 0.0001:
        raise ValueError("error in comparing the csv files: viertel doesnt sum to correct values")
    viertel.value_calc += diffs.median()
    result = viertel.value_calc.to_frame()
    result = result.loc[result.index.map(lambda x: x.minute == 0)]
    result.index -= timedelta(hours=1)
    result = result.reset_index()
    result = result.rename(columns={"date_time": "start", "value_calc": "state"})
    result['statistic_id'] = "sensor.energy"
    result['unit'] = "kWh"
    result['sum'] = result.state - result.state[0]
    result = result[['statistic_id', 'unit', 'start', 'state', 'sum']]
    result = result.dropna()
    result.to_csv("output.csv", index=False, date_format="%d.%m.%Y %H:%M")
