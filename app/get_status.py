# https://api.mcsrvstat.us/2/73.5.182.165

import requests
import json


def get_public_ip(v: int = 4) -> str:
    url = {
        4: "http://ipv4.icanhazip.com",
        6: "http://ipv6.icanhazip.com"
    }
    ip = requests.request("get", f"{url[v]}").text
    return ip


def get_status():
    data = requests.request("get", f"https://api.mcsrvstat.us/2/{get_public_ip(4)}")
    print(data.text)
    status = json.loads(data.text)
    print(status['debug'])
    
# for key in list(str(each) for each in info.keys()):
#     print(f"{key}:{str(info.get(key))}")


def main():
    get_status()
    pass


if __name__ == '__main__':
    main()
