"""requester"""
import time
import random
import warnings
import requests

warnings.filterwarnings("ignore")  # Disable SSL related warnings


def requester(url, data, headers, GET, delay):
    time.sleep(delay)
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.3",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.1",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.",
        "Mozilla/5.0 (X11; Linux i686; rv:127.0) Gecko/20100101 Firefox/127.0",
        "Mozilla/5.0 (X11; U; Linux 2.4.2-2 i586; en-US; m18) Gecko/20010131 Netscape6/6.01",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/25.0 Chrome/121.0.0.0 Safari/537.3",
        "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/525.19 (KHTML, like Gecko) Chrome/0.2.153.1 Safari/525.19",
    ]

    if headers:
        if "User-Agent" not in headers:
            headers["User-Agent"] = random.choice(user_agents)

    if GET:
        response = requests.get(
            url, params=data, headers=headers, verify=False, timeout=1
        )
    else:
        response = requests.post(
            url, data=data, headers=headers, verify=False, timeout=1
        )

    return response
