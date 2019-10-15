import requests


def check_internet_connection():
    try:
        url = 'https://www.google.com/'
        response = requests.head(url)
        return response.ok
    except:
        return False
