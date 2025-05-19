import json

import requests


def main() -> None:
    res = requests.get(
        "https://tapi.pureapk.com/v3/get_app_his_version?package_name=com.paypal.android.p2pmobile&hl=en",
        headers={
            "Ual-Access-Businessid": "projecta",
            "Ual-Access-ProjectA": r'{"device_info":{"os_ver":"36"}}',
        },
        timeout=10,
    )
    print(res.status_code)
    versions: list[dict] = res.json()["version_list"]
    for v in versions:
        print(f"{v["version_name"]} ({v['version_code']}) - {','.join(v["native_code"])}")
    print(
        json.dumps(
            {
                k: v
                for k, v in versions[1].items()
                if k
                not in {
                    "screenshots",
                    "icon",
                    "permissions",
                    "ai_headline_info",
                    "banner",
                    "tags",
                    "developer_open_config",
                    "category_open_config",
                    "pre_register_info",
                    "official_open_config",
                    "version_open_config",
                    "description",
                    "tubes",
                }
            },
        ),
    )


if __name__ == "__main__":
    main()
