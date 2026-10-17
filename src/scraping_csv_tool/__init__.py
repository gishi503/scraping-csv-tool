import requests
from bs4 import BeautifulSoup


def main() -> None:
    res = requests.get("https://books.toscrape.com/", timeout=10)
    soup = BeautifulSoup(res.text, "html.parser")
    for book in soup.select("article.product_pod h3 a")[:5]:
        print(book["title"])