# https://api.mcsrvstat.us/2/73.5.182.165

import requests
import json
from ipaddress import ip_address

# TODO: caching


def get_public_ip(v: int = 4) -> dict:
    # TODO: branch ip
    try:
        # should add check to verify formatting
        url = {
            4: "http://ipv4.icanhazip.com",
            6: "http://ipv6.icanhazip.com"
        }
        ip = requests.request("get", f"{url[v]}")

        # return {"type": v, "address": ip.text.strip()}
        if len(str(ip_address(ip.text.strip()))) > 0:
            return {"type": v, "address": ip.text.strip()}
        else:
            return {"type": 0, "address": "0.0.0.0"}
    except ValueError:
        return {"type": 0, "address": "0.0.0.0"}


def get_status(ip: str = "127.0.0.1") -> json:
    # todo: branch status
    # mcsrvstat seems to support fqdn or ipv4, but not ipv6
    data = requests.request("get", f"https://api.mcsrvstat.us/2/{ip}")
    # data = "{success}"
    print(data.text)
    status = json.loads(data.text)
    return status


def main():
    ip_info = get_public_ip()
    print(ip_info)
    if ip_info["type"] == 4:
        status = get_status(ip_info["address"])
        print(status)
    else:
        raise ValueError
    

if __name__ == '__main__':
    main()
