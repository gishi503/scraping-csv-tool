"""集めたデータをCSVに保存する処理。"""

import csv
from pathlib import Path

# CSVの列: (データのキー, 見出し)
# 依頼主がExcelで開くことを想定して、見出しは日本語にする
COLUMNS = [
    ("title", "タイトル"),
    ("price", "価格（ポンド）"),
    ("stock", "在庫"),
    ("rating", "評価（1〜5）"),
]


def save_csv(books: list[dict], path: Path) -> None:
    """本のリストをCSVに保存する。

    文字コードは utf-8-sig（BOM付きUTF-8）にする。
    BOMがないと、Excelでダブルクリックして開いたときに日本語が文字化けする。
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([header for _, header in COLUMNS])
        for book in books:
            writer.writerow([book[key] for key, _ in COLUMNS])
