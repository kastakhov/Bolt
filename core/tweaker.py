"""tweaker"""
import random
import re
from core.config import tokenPattern


def tweaker(data, strategy, index=0, seeds=[None, None]):
    """tweaker"""
    digits = seeds[0]
    alphabets = seeds[1]
    newData = {}

    if strategy == "clear":
        for name, value in data.items():
            if re.match(tokenPattern, value):
                value = ""
            newData[name] = value
        return newData

    if strategy == "remove":
        for name, value in data.items():
            if not re.match(tokenPattern, value):
                newData[name] = value
        return newData

    if strategy == "break":
        for name, value in data.items():
            if re.match(tokenPattern, value):
                value = value[:index]
                for _ in index:
                    value += random.choice(digits + alphabets)
            newData[name] = value
        return newData

    if strategy == "generate":
        for name, value in data.items():
            if re.match(tokenPattern, value):
                newToken = ""
                for char in list(value):
                    if char in digits:
                        newToken += random.choice(digits)
                    elif char in alphabets:
                        newToken += random.choice(alphabets)
                    else:
                        newToken += char
                newData[name] = newToken
            else:
                newData[name] = value
        return newData

    if strategy == "replace":
        for name, value in data.items():
            if re.match(tokenPattern, value):
                value

    return newData
