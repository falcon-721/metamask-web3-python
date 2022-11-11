import json
from urllib.request import Request, urlopen
import requests
from bs4 import BeautifulSoup

def getAPIResponse(url):
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    html = urlopen(req).read()
    response = json.loads(html)
    return response