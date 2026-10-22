"""books.toscrape.com から本の一覧を取得する処理。"""

import logging
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)

BASE_URL = "https://books.toscrape.com/"

# サーバーに負担をかけないよう、ページごとに待つ秒数
WAIT_SECONDS = 1.0

# 通信に失敗したときに試す回数（1回目を含む）
MAX_ATTEMPTS = 3

# 相手のサーバーに「何のアクセスか」を伝えるため、ツール名と連絡先を名乗る
HEADERS = {
    "User-Agent": "scraping-csv-tool/0.1 (+https://github.com/gishi503/scraping-csv-tool)"
}

# 評価はクラス名に英単語で入っている（例: "star-rating Three"）ので数値に変換する
RATING_WORDS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


class FetchError(Exception):
    """ページを取得できなかったときのエラー。"""


class ParseError(Exception):
    """HTMLから必要な項目を取り出せなかったときのエラー。"""


def _should_retry(error: requests.RequestException) -> bool:
    """やり直せば成功する見込みのあるエラーかどうか。"""
    response = error.response
    if response is None:
        # タイムアウトや接続エラー（一時的なことが多い）
        return True
    # 429: アクセスが多すぎる / 5xx: サーバー側の一時的なエラー
    # 404 などそれ以外の 4xx は、何度やっても結果が変わらない
    return response.status_code == 429 or response.status_code >= 500


def fetch_html(url: str) -> str:
    """URLのHTMLを取得する。一時的なエラーなら、待ち時間を延ばしながらやり直す。"""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            res = requests.get(url, headers=HEADERS, timeout=10)
            res.raise_for_status()  # 404 や 500 などをエラーとして扱う
        except requests.RequestException as e:
            if not _should_retry(e) or attempt == MAX_ATTEMPTS:
                raise FetchError(f"{url} を取得できませんでした: {e}") from e
            wait = 2**attempt  # 2秒 → 4秒 と延ばす
            logger.warning(
                "取得に失敗しました（%d/%d回目）。%d秒後にやり直します: %s",
                attempt,
                MAX_ATTEMPTS,
                wait,
                e,
            )
            time.sleep(wait)
        else:
            res.encoding = "utf-8"
            return res.text

    raise AssertionError("ここには来ない")


def _select(article: Tag, selector: str) -> Tag:
    """select_one と同じだが、見つからなければ ParseError にする。"""
    element = article.select_one(selector)
    if element is None:
        raise ParseError(f"「{selector}」が見つかりません")
    return element


def parse_book(article: Tag) -> dict:
    """本1冊分の <article> から4項目を取り出す。"""
    title = _select(article, "h3 a").get("title")
    if not title:
        raise ParseError("タイトルが空です")

    price_text = _select(article, "p.price_color").get_text(strip=True)
    try:
        price = float(price_text.lstrip("£"))
    except ValueError as e:
        raise ParseError(f"価格を数値にできません: {price_text!r}") from e

    stock = _select(article, "p.availability").get_text(strip=True)

    rating_classes = _select(article, "p.star-rating").get("class", [])
    rating = next((RATING_WORDS[c] for c in rating_classes if c in RATING_WORDS), None)

    return {
        "title": title,
        "price": price,
        "stock": stock,
        "rating": rating,
    }


def parse_page(html: str, page_url: str) -> tuple[list[dict], str | None]:
    """一覧ページ1枚分のHTMLから、全冊の情報と次のページのURLを取り出す。

    取り出せない本があっても止めずに飛ばし、ログに残す。
    最後のページでは、次のページのURLは None になる。
    """
    soup = BeautifulSoup(html, "html.parser")

    books = []
    for i, article in enumerate(soup.select("article.product_pod"), start=1):
        try:
            books.append(parse_book(article))
        except ParseError as e:
            logger.warning("%s の %d冊目を飛ばしました: %s", page_url, i, e)

    # 「next」のリンクは相対パスで、ページによって書き方が変わる
    # （1ページ目は "catalogue/page-2.html"、2ページ目以降は "page-3.html"）
    # urljoin で今のページのURLとつなげれば、どちらでも正しいURLになる
    next_link = soup.select_one("li.next a")
    next_url = urljoin(page_url, next_link["href"]) if next_link else None

    return books, next_url


def scrape_all(start_url: str = BASE_URL, max_pages: int | None = None) -> list[dict]:
    """「next」をたどって全ページを巡回し、すべての本の情報を集める。

    途中でページを取得できなくなったり、Ctrl+C で止めたりした場合は、
    そこまでに集めた分を返す（何も残らない、ということを避ける）。
    max_pages を指定すると、そのページ数で止める（動作確認用）。
    """
    all_books = []
    url = start_url
    page = 0

    try:
        while url:
            page += 1
            try:
                html = fetch_html(url)
            except FetchError as e:
                logger.error("%s。ここまでの %d冊で終了します", e, len(all_books))
                break

            books, url = parse_page(html, url)
            all_books.extend(books)
            logger.info(
                "%dページ目: %d冊（累計 %d冊）", page, len(books), len(all_books)
            )

            if max_pages and page >= max_pages:
                break
            if url:
                time.sleep(WAIT_SECONDS)
    except KeyboardInterrupt:
        logger.warning("中断しました。ここまでの %d冊を保存します", len(all_books))

    return all_books
