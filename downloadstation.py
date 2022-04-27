import os

import requests
from dotenv import load_dotenv

load_dotenv()
NAS_HOST = os.getenv('NAS_HOST')
NAS_USER = os.getenv('NAS_USER')
NAS_PASS = os.getenv('NAS_PASS')


class SynologyAPI:
    def __init__(self, host):
        self.host = host
        self.session = requests.Session()
        res = self.session.get(f'{self.host}/webapi/query.cgi?api=SYNO.API.Info&version=1&method=query&query=all')
        self.apis = res.json()['data']

    def call(self, api, version, method, params=None):
        if api not in self.apis:
            raise ValueError(f"API '{api}' is not supported")
        api_info = self.apis[api]
        if not api_info['minVersion'] <= version <= api_info['maxVersion']:
            raise ValueError(f"{api} only supports version {api_info['minVersion']} up to {api_info['minVersion']}")

        if params is None:
            params = {}
        else:
            params = params.copy()

        params['api'] = api
        params['version'] = version
        params['method'] = method

        res = self.session.post(f"{self.host}/webapi/{api_info['path']}", data=params)
        res = res.json()
        if res['success']:
            return res['data']
        else:
            raise IOError(f"API Error: {res}")

    def login(self, username, password, session=None):
        params = {'account': username, 'passwd': password}
        if session is not None:
            params['session'] = session
        self.call('SYNO.API.Auth', 6, 'login', params)


def main():
    api = SynologyAPI(NAS_HOST)

    api.login(NAS_USER, NAS_PASS, 'DownloadStation')

    res = api.call('SYNO.DownloadStation.Task', 1, 'list')
    for t in res['tasks']:
        print(f"{t['title']} - {t['status']}")


if __name__ == '__main__':
    main()
