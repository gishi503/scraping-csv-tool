import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

from scraping_csv_tool.exporter import save_csv
from scraping_csv_tool.scraper import scrape_all

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="books.toscrape.com の本の一覧を集めてCSVに保存します。"
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="保存先のCSVファイル（省略時は output/books_日時.csv）",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        help="取得するページ数の上限（動作確認用。省略時は全ページ）",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    output = args.output or Path("output") / f"books_{datetime.now():%Y%m%d_%H%M%S}.csv"

    books = scrape_all(max_pages=args.max_pages)
    if not books:
        logger.error("1冊も取得できなかったため、CSVは作成しません")
        sys.exit(1)

    try:
        save_csv(books, output)
    except OSError as e:
        # 保存先のフォルダに書き込めない、ファイルをExcelで開いたまま、など
        logger.error("CSVを保存できませんでした: %s", e)
        sys.exit(1)

    logger.info("合計 %d冊を %s に保存しました", len(books), output)
