import requests
from requests import Response, RequestException

def fetch_article(url : str) -> Response | RequestException:
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except RequestException as e:
        return e
    return response


def main():
    print(fetch_article('https://addyosmani.com/blog/factory-model/').text)

if __name__ == "__main__":
    main()