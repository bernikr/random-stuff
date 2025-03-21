from datetime import timedelta
from pathlib import Path

import pandas as pd

# to be used with: https://github.com/klausj1/homeassistant-statistics
# IMPORTANT: Output tz is UTC

if __name__ == "__main__":
    zaehler_csv = list(Path(__file__).parent.glob("ZAEHLERSTAENDE-*.csv"))
    if len(zaehler_csv) != 1:
        msg = "Supply exactly 1 ZAEHLERSTAENDE csv file"
        raise FileNotFoundError(msg)
    viertel_csv = list(Path(__file__).parent.glob("VIERTELSTUNDENWERTE_ECONTROL-*.csv"))
    if len(viertel_csv) != 1:
        msg = "Supply exactly 1 VIERTELSTUNDENWERTE_ECONTROL csv file"
        raise FileNotFoundError(msg)

    zaehler = (
        pd.read_csv(
            zaehler_csv[0],
            sep=";",
            usecols=[0, 1, 2],
            parse_dates=[0],
            decimal=",",
            names=["date", "value", "anmerkung"],
            header=0,
            dayfirst=True,
        )
        .dropna(subset=["value"])
        .set_index("date")
    )
    zaehler = zaehler.drop(zaehler[zaehler.anmerkung.isna() != True].index)  # noqa: E712
    viertel = (
        pd.read_csv(
            viertel_csv[0], sep=";", usecols=[0, 3], parse_dates=[0], decimal=",", names=["date_time", "used"], header=0
        )
        .dropna()
        .set_index("date_time")
    )
    zaehler.index = (zaehler.index + timedelta(days=1)).tz_localize("Europe/Vienna").tz_convert("UTC")  # type: ignore
    viertel.index = pd.to_datetime(viertel.index, utc=True)
    viertel.loc[viertel.index[0] - timedelta(minutes=15)] = 0  # type: ignore
    viertel = viertel.sort_index()
    viertel["value_calc"] = viertel.used.cumsum()
    diffs = zaehler.join(viertel, how="inner")
    diffs = diffs.value - diffs.value_calc
    print(f"difference deviation: {diffs.max() - diffs.min()}")
    if diffs.max() - diffs.min() > 0.01:  # noqa: PLR2004
        msg = "error in comparing the csv files: viertel doesnt sum to correct values"
        raise ValueError(msg)
    viertel.value_calc += diffs.median()
    result = viertel.value_calc.to_frame()
    result = result.loc[result.index.map(lambda x: x.minute == 0)]
    result.index -= timedelta(hours=1)
    result = result.reset_index()
    result = result.rename(columns={"date_time": "start", "value_calc": "state"})
    result["statistic_id"] = "sensor.energy"
    result["unit"] = "kWh"
    result["sum"] = result.state - result.state[0]
    result = result[["statistic_id", "unit", "start", "state", "sum"]]
    result = result.dropna()
    result.to_csv("output.csv", index=False, date_format="%d.%m.%Y %H:%M", float_format="%.3f")
