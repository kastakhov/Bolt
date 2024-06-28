"""bolt"""

import concurrent.futures
from pathlib import Path

import argparse
import json
import random
import re
import statistics

from fuzzywuzzy import fuzz, process
from core.entropy import isRandom
from core.datanize import datanize
from core.prompt import prompt
from core.photon import photon
from core.tweaker import tweaker
from core.evaluate import evaluate
from core.ranger import ranger
from core.zetanize import zetanize
from core.requester import requester
from core.utils import (
    extractHeaders,
    strength,
    isProtected,
    stringToBinary,
    longestCommonSubstring,
)


from core.colors import green, yellow, end, run, good, info, bad, white, red

lightning = "\033[93;5m⚡\033[0m"


def banner():
    """banner"""
    print(
        f"""
     {yellow}⚡ {white}BOLT{yellow}  ⚡{end}
    """
    )


banner()

parser = argparse.ArgumentParser()
parser.add_argument("-u", help="target url", dest="target")
parser.add_argument("-t", help="number of threads", dest="threads", type=int)
parser.add_argument("-l", help="levels to crawl", dest="level", type=int)
parser.add_argument("--delay", help="delay between requests", dest="delay", type=int)
parser.add_argument("--timeout", help="http request timeout", dest="timeout", type=int)
parser.add_argument(
    "--headers", help="http headers", dest="add_headers", nargs="?", const=True
)
args = parser.parse_args()

if not args.target:
    print("\n" + parser.format_help().lower())
    quit()

if type(args.add_headers) == bool:
    headers = extractHeaders(prompt())
elif type(args.add_headers) == str:
    headers = extractHeaders(args.add_headers)
else:
    from core.config import headers

target = args.target
delay = args.delay or 0
level = args.level or 2
timeout = args.timeout or 20
threadCount = args.threads or 2

allTokens = []
weakTokens = []
tokenDatabase = []
insecureForms = []

print(" %s Phase: Crawling %s[%s1/6%s]%s" % (lightning, green, end, green, end))
dataset = photon(target, headers, level, threadCount)
allForms = dataset[0]
print(
    "\r%s Crawled %i URL(s) and found %i form(s).%-10s"
    % (info, dataset[1], len(allForms), " ")
)
print(" %s Phase: Evaluating %s[%s2/6%s]%s" % (lightning, green, end, green, end))

evaluate(allForms, weakTokens, tokenDatabase, allTokens, insecureForms)

if weakTokens:
    print("%s Weak token(s) found" % good)
    for weakToken in weakTokens:
        url = list(weakToken.keys())[0]
        token = list(weakToken.values())[0]
        print("%s %s %s" % (info, url, token))

if insecureForms:
    print("%s Insecure form(s) found" % good)
    for insecureForm in insecureForms:
        url = list(insecureForm.keys())[0]
        action = list(insecureForm.values())[0]["action"]
        form = action.replace(target, "")
        if form:
            print("%s %s %s[%s%s%s]%s" % (bad, url, green, end, form, green, end))

print(" %s Phase: Comparing %s[%s3/6%s]%s" % (lightning, green, end, green, end))
uniqueTokens = set(allTokens)
if len(uniqueTokens) < len(allTokens):
    print("%s Potential Replay Attack condition found" % good)
    print("%s Verifying and looking for the cause" % run)
    replay = False
    for each in tokenDatabase:
        url, token = next(iter(each.keys())), next(iter(each.values()))
        for each2 in tokenDatabase:
            url2, token2 = next(iter(each2.keys())), next(iter(each2.values()))
            if token == token2 and url != url2:
                print(
                    "%s The same token was used on %s%s%s and %s%s%s"
                    % (good, green, url, end, green, url2, end)
                )
                replay = True
    if not replay:
        print("%s Further investigation shows that it was a false positive.")

p = Path(__file__).parent.joinpath("db/hashes.json")
with p.open("r", encoding="latin1") as f:
    hashPatterns = json.load(f)

if not allTokens:
    print(f"{bad} No CSRF protection to test")
    quit()

aToken = allTokens[0]
matches = []
for element in hashPatterns:
    pattern = element["regex"]
    if re.match(pattern, aToken):
        for name in element["matches"]:
            matches.append(name)
if matches:
    print(f"{info} Token matches the pattern of following hash type(s):")
    for name in matches:
        print(f"    {yellow}>{end} {name}")


def fuzzy(tokens):
    """fuzzy"""
    averages = []

    for token in tokens:
        sameTokenRemoved = False
        result = process.extract(token, tokens, scorer=fuzz.partial_ratio)
        scores = []
        for each in result:
            score = each[1]
            if score == 100 and not sameTokenRemoved:
                sameTokenRemoved = True
                continue
            scores.append(score)
        average = statistics.mean(scores)
        averages.append(average)

    return statistics.mean(averages)


try:
    similarity = fuzzy(allTokens)
    print(
        "%s Tokens are %s%i%%%s similar to each other on an average"
        % (info, green, similarity, end)
    )
except statistics.StatisticsError:
    print("%s No CSRF protection to test" % bad)
    quit()


def staticParts(allTokens):
    """staticParts"""
    strings = list(set(allTokens.copy()))
    commonSubstrings = {}

    for theString in strings:
        strings.remove(theString)

        for string in strings:
            commonSubstring = longestCommonSubstring(theString, string)
            if commonSubstring not in commonSubstrings:
                commonSubstrings[commonSubstring] = []
            if len(commonSubstring) > 2:
                if theString not in commonSubstrings[commonSubstring]:
                    commonSubstrings[commonSubstring].append(theString)
                if string not in commonSubstrings[commonSubstring]:
                    commonSubstrings[commonSubstring].append(string)

    return commonSubstrings


result = {k: v for k, v in staticParts(allTokens).items() if v}

if result:
    print(f"{info} Common substring found")
    print(json.dumps(result, indent=4))

simTokens = []

print(f" {lightning} Phase: Observing {green}[{end}4/6{green}]{end}")
print(f"{info} 100 simultaneous requests are being made, please wait.")


def extractForms(url):
    """extractForms"""
    response = requester(url, {}, headers, True, 0).text
    forms = zetanize(url, response)

    for each in forms.values():
        inputs = each["inputs"]
        for inp in inputs:
            value = inp["value"]
            if value and re.match(r"^[\w\-_]+$", value):
                if strength(value) > 10:
                    simTokens.append(value)


while True:
    sample = random.choice(tokenDatabase)
    goodToken = list(sample.values())[0]
    if len(goodToken) > 0:
        goodCandidate = list(sample.keys())[0]
        break

threadpool = concurrent.futures.ThreadPoolExecutor(max_workers=30)
futures = (
    threadpool.submit(extractForms, goodCandidate)
    for goodCandidate in [goodCandidate] * 30
)

for _ in concurrent.futures.as_completed(futures):
    pass

if simTokens:
    if len(set(simTokens)) < len(simTokens):
        print(f"{good} Same tokens were issued for simultaneous requests.")
    else:
        print(simTokens)
else:
    print(f"{info} Different tokens were issued for simultaneous requests.")

print(f" {lightning} Phase: Testing {green}[{end}5/6{green}]{end}")

parsed = ""
found = False

print(f"{run} Finding a suitable form for further testing. It may take a while.")
for form_dict in allForms:
    for url, forms in form_dict.items():
        parsed = datanize(forms, tolerate=True)
        if parsed:
            found = True
            break

    if found:
        break

if not parsed:
    quit(f"{bad} No suitable form found for testing.")

origGET = parsed[0]
origUrl = parsed[1]
origData = parsed[2]

print(f"{run} Making a request with CSRF token for comparison.")
response = requester(origUrl, origData, headers, origGET, 0)
originalCode = response.status_code
originalLength = len(response.text)
print(f"{info} Status Code: {originalCode}")
print(f"{info} Content Length: {originalLength}")
print(f"{run} Checking if the response is dynamic.")

response = requester(origUrl, origData, headers, origGET, 0)
secondLength = len(response.text)

if originalLength != secondLength:
    print(f"{info} Response is dynamic.")
    tolerableDifference = abs(originalLength - secondLength)
else:
    print(f"{info} Response isn't dynamic.")
    tolerableDifference = 0

print(f"{run} Emulating a mobile browser")
print(f"{run} Making a request with mobile browser")
headers["User-Agent"] = "Mozilla/4.0 (compatible; MSIE 5.5; Windows CE; PPC; 240x320)"
response = requester(origUrl, {}, headers, True, 0).text
parsed = zetanize(origUrl, response)

if isProtected(parsed):
    print(f"{bad} CSRF protection is enabled for mobile browsers as well.")
else:
    print(f"{good} CSRF protection isn't enabled for mobile browsers.")

print(f"{run} Making a request without CSRF token parameter.")

data = tweaker(origData, "remove")
response = requester(origUrl, data, headers, origGET, 0)
if response.status_code == originalCode:
    if str(originalCode)[0] in ["4", "5"]:
        print(f"{bad} It didn't work")
    else:
        difference = abs(originalLength - len(response.text))
        if difference <= tolerableDifference:
            print(f"{good} It worked!")
else:
    print(f"{bad} It didn't work")

print(f"{run} Making a request without CSRF token parameter value.")
data = tweaker(origData, "clear")

response = requester(origUrl, data, headers, origGET, 0)
if response.status_code == originalCode:
    if str(originalCode)[0] in ["4", "5"]:
        print(f"{bad} It didn't work")
    else:
        difference = abs(originalLength - len(response.text))
        if difference <= tolerableDifference:
            print(f"{good} It worked!")
else:
    print(f"{bad} It didn't work")


seeds = ranger(allTokens)

print(f"{run} Checking if tokens are checked to a specific length")

for index in range(len(allTokens[0])):
    data = tweaker(origData, "replace", index=index, seeds=seeds)
    response = requester(origUrl, data, headers, origGET, 0)
    if response.status_code == originalCode:
        if str(originalCode)[0] in ["4", "5"]:
            break
        else:
            difference = abs(originalLength - len(response.text))
            if difference <= tolerableDifference:
                print(f"{good} Last {index+1} chars of token aren't being checked")
    else:
        break

print(f"{run} Generating a fake token.")

data = tweaker(origData, "generate", seeds=seeds)
print(f"{run} Making a request with the self generated token.")

response = requester(origUrl, data, headers, origGET, 0)
if response.status_code == originalCode:
    if str(originalCode)[0] in ["4", "5"]:
        print(f"{bad} It didn't work")
    else:
        difference = abs(originalLength - len(response.text))
        if difference <= tolerableDifference:
            print(f"{good} It worked!")
else:
    print(f"{bad} It didn't work")

print(f" {lightning} Phase: Analysing {green}[{end}6/6{green}]{end}")

binary = stringToBinary("".join(allTokens))
result = isRandom(binary)
for name, result in result.items():
    if not result:
        print(f"{good} {name} : {green}non-random{end}")
    else:
        print(f"{bad} {name} : {red}random{end}")
