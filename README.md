# scraping-csv-tool

Webサイトの一覧ページを最後のページまで自動で巡回し、集めた情報を **Excelでそのまま開けるCSV** に保存するPythonツールです。

練習用サイト [Books to Scrape](https://books.toscrape.com/)（スクレイピング練習のために公開されているサイト）を対象に、全50ページ・1,000冊の **タイトル・価格・在庫・評価** を約1分40秒で集めます。

## できること

- **全ページを自動で巡回**：「次へ」のリンクをたどり、最後のページまで集めます
- **Excelで文字化けしないCSV**：BOM付きUTF-8で保存するので、ダブルクリックで開けます
- **そのまま使える形に整える**：価格は記号を外した数値に、評価（星の数）は1〜5の数値に変換します
- **途中で止まりにくい**
  - 通信が一時的に失敗したときは、待ち時間を延ばしながら最大3回までやり直します
  - 項目が欠けている商品があっても全体は止めず、その商品だけ飛ばしてログに残します
  - 途中でページが取れなくなったり Ctrl+C で止めたりしても、それまでに集めた分は保存します
- **相手のサーバーに配慮**：1ページごとに1秒待ち、ツール名と連絡先を名乗ってアクセスします

## 出力例

[examples/sample.csv](examples/sample.csv)（先頭10件）

| タイトル | 価格（ポンド） | 在庫 | 評価（1〜5） |
|---|---|---|---|
| A Light in the Attic | 51.77 | In stock | 3 |
| Tipping the Velvet | 53.74 | In stock | 1 |
| Soumission | 50.1 | In stock | 1 |
| Sharp Objects | 47.82 | In stock | 4 |
| Sapiens: A Brief History of Humankind | 54.23 | In stock | 5 |

実行中は進み具合が表示されます。

```
21:13:24 [INFO] 1ページ目: 20冊（累計 20冊）
21:13:25 [INFO] 2ページ目: 20冊（累計 40冊）
...
21:15:02 [INFO] 50ページ目: 20冊（累計 1000冊）
21:15:02 [INFO] 合計 1000冊を output/books_20261022_211324.csv に保存しました
```

## 使い方

[uv](https://docs.astral.sh/uv/) が必要です。

```bash
git clone https://github.com/gishi503/scraping-csv-tool.git
cd scraping-csv-tool
uv run scraping-csv-tool
```

`output/books_日時.csv` に保存されます。

| オプション | 説明 |
|---|---|
| `-o`, `--output` | 保存先のCSVファイルを指定する |
| `--max-pages` | 取得するページ数の上限（動作確認用） |

```bash
# 3ページだけ取得して、指定したファイルに保存する
uv run scraping-csv-tool --max-pages 3 -o books.csv
```

## ファイル構成

```
src/scraping_csv_tool/
├── __init__.py   # 入口（オプションの読み取り、ログ設定、全体の流れ）
├── scraper.py    # ページの取得・解析・巡回、エラー時のやり直し
└── exporter.py   # CSVへの保存
```

取得（`scraper.py`）と保存（`exporter.py`）を分けているので、対象のサイトや出力形式（Excel、Googleスプレッドシートなど）が変わっても、該当する部分だけ差し替えれば対応できます。

## 使用技術

- Python 3.14
- requests / Beautiful Soup 4
- uv（パッケージ管理）、Ruff（コードのチェック・整形）

## ご依頼について

同じ仕組みで、次のような作業を自動化できます。

- 競合サイトや通販サイトの価格・在庫の定期チェック
- 求人・不動産・店舗情報などの一覧の収集
- 集めたデータのExcel・Googleスプレッドシートへの出力

対象サイトの利用規約と robots.txt を確認し、収集が認められている範囲で対応します。
