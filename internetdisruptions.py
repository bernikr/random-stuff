import os
from dataclasses import dataclass
from datetime import datetime

import dateutil.parser
import pytz
import requests
from dotenv import load_dotenv

load_dotenv()
INFLUX_URL = os.getenv('INFLUX_URL')
INFLUX_TOKEN = os.getenv('INFLUX_TOKEN')
INFLUX_ORG = os.getenv('INFLUX_ORG')

start = "2020-05-01"
#start = "2021-11-01"
stop = "now()"

query = f"""import "math"
from(bucket: "collectd")
  |> range(start: {start}, stop: {stop})
  |> filter(fn: (r) => r["_measurement"] == "ping_value")
  |> filter(fn: (r) => r["_field"] == "value")
  |> filter(fn: (r) => r["host"] == "OpenWrt")
  |> filter(fn: (r) => r["type"] == "ping_droprate")
  |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)
  |> pivot(rowKey:["_time"], columnKey: ["type_instance"], valueColumn: "_value")
  |> map(fn: (r) => ({{ r with _value: math.mMin(x: r["1.1.1.1"], y: r["8.8.8.8"])}}))
  |> keep(columns: ["_time", "_value"])"""


def format_datatime(dt: datetime):
    return dt.astimezone(pytz.timezone('Europe/Vienna')).strftime("%d.%m.%Y %H:%M")


@dataclass
class Disruption:
    start: datetime
    end: datetime

    @property
    def duration(self):
        return self.end - self.start

    def __repr__(self):
        return f"{format_datatime(self.start)} - {format_datatime(self.end)}; Duration: {self.duration}"

def parse_disruptions(res):
    current_start = None
    for i, line in enumerate(res.iter_lines()):
        if i == 0:
            assert line == b',result,table,_time,_value', f"CSV Format changed, new format: `{line}`"
            continue
        if line == b'':
            continue
        _, _, _, t, v = line.split(b',')
        try:
            v = float(v)
        except ValueError:
            v = 0
        if current_start is None and v > 0.7:
            current_start = t
        elif current_start is not None and v < 0.3:
            yield(Disruption(start=dateutil.parser.isoparse(current_start.decode()),
                             end=dateutil.parser.isoparse(t.decode())))
            current_start = None


def main():
    headers = {
        "Authorization": f"Token {INFLUX_TOKEN}",
        "Content-Type": "application/vnd.flux",
    }
    r = requests.post(f"{INFLUX_URL}/api/v2/query?org={INFLUX_ORG}", headers=headers, data=query, stream=True)
    for dis in parse_disruptions(r):
        print(dis)




if __name__ == '__main__':
    main()
