"""utils"""
import re
from core.config import tokenPattern


def longestCommonSubstring(s1, s2):
    """longestCommonSubstring"""
    m = [[0] * (1 + len(s2)) for i in range(1 + len(s1))]
    longest, x_longest = 0, 0
    for x in range(1, 1 + len(s1)):
        for y in range(1, 1 + len(s2)):
            if s1[x - 1] == s2[y - 1]:
                m[x][y] = m[x - 1][y - 1] + 1
                if m[x][y] > longest:
                    longest = m[x][y]
                    x_longest = x
            else:
                m[x][y] = 0
    return s1[x_longest - longest : x_longest]


def stringToBinary(string):
    """stringToBinary"""
    return "".join(format(ord(x), "b") for x in string)


def strength(string):
    """strength"""
    digits = re.findall(r"\d", string)
    lowerAlphas = re.findall(r"[a-z]", string)
    upperAlphas = re.findall(r"[A-Z]", string)
    entropy = len(set(digits + lowerAlphas + upperAlphas))
    if not digits:
        entropy = entropy / 2

    return entropy


def isProtected(parsed):
    """isProtected"""
    protected = False
    parsedForms = list(parsed.values())

    for oneForm in parsedForms:
        inputs = oneForm["inputs"]
        for inp in inputs:
            value = inp["value"]
            if re.match(tokenPattern, value):
                protected = True

    return protected


def extractHeaders(headers):
    """extractHeaders"""
    headers = headers.replace("\\n", "\n")
    sorted_headers = {}
    matches = re.findall(r"(.*):\s(.*)", headers)

    for match in matches:
        header = match[0]
        value = match[1]
        try:
            if value[-1] == ",":
                value = value[:-1]
            sorted_headers[header] = value
        except IndexError:
            pass

    return sorted_headers


def getUrl(url, data, GET):
    """getUrl"""
    if GET:
        return url.split("?")[0]

    return url


def getParams(url, data, GET):
    """getParams"""
    params = {}
    if GET:
        if "=" in url:
            data = url.split("?")[1]
            if data[:1] == "?":
                data = data[1:]
        else:
            data = ""

    parts = data.split("&")

    for part in parts:
        each = part.split("=")
        try:
            params[each[0]] = each[1]
        except IndexError:
            params = None

    return params


def remove_file(url):
    """remove_file"""
    if url.count("/") > 2:
        replacable = re.search(r"/[^/]*?$", url).group()
        if replacable != "/":
            return url.replace(replacable, "")
        else:
            return url

    return url
