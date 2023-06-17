# 認証のためのコード
from google.colab import auth
auth.authenticate_user()
import gspread
from google.auth import default
creds, _ = default()
gc = gspread.authorize(creds)

# 使用ライブラリ
import difflib
import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime
import pytz


# スプレッドシートを開く
spreadsheet = gc.open("webscrapingtest1.0") # スプレットシートのファイル名を入力
worksheet1 = spreadsheet.get_worksheet(0)  # Sheet1

col = 2  # B列

# ワークシート1の列Bを順番に処理
for row in range(2, worksheet1.row_count + 1):

    url = worksheet1.cell(row, col).value  # スプレットシートのURLを取得

    if not url:  # URLがなければループを抜ける
        break

    # 前回のシートと現在のシートを取得または作成
    last_sheet_title = f"LastSheet{row}"
    curr_sheet_title = f"CurrSheet{row}"

    last_sheet = None
    curr_sheet = None
    for sheet in spreadsheet.worksheets():
        if sheet.title == last_sheet_title:
            last_sheet = sheet
        elif sheet.title == curr_sheet_title:
            curr_sheet = sheet

    if last_sheet is None:
        last_sheet = spreadsheet.add_worksheet(title=last_sheet_title, rows="100", cols="20")
    if curr_sheet is None:
        curr_sheet = spreadsheet.add_worksheet(title=curr_sheet_title, rows="100", cols="20")

    # 現在の日付を取得
    current_date = datetime.now(pytz.timezone('Asia/Tokyo')).strftime('%Y-%m-%d')

    #ページのHMTLを取得。できなかった場合、エラー処理をする。
    try:
        response = requests.get(url)
    except requests.exceptions.RequestException as e:  # すべてのrequestsエラーを捕捉
        worksheet1.update_cell(row, col + 1, f"エラー: {e}")
        continue

    soup = BeautifulSoup(response.content, 'html.parser', from_encoding='utf-8')  # 取得したHTMLを解析

    try:
        curr_sheet.update_cell(1,1, (soup.get_text()))  # 差分比較用に現在のシートに書き込む
    except gspread.exceptions.APIError as e:  # 書き込みエラーを捕捉
        worksheet1.update_cell(row, col + 1, f"エラー: {e}")
        continue

    # 前回のシートと現在のシートを比較
    last_sheet_values = last_sheet.get_all_values()
    curr_sheet_values = curr_sheet.get_all_values()

    diff = difflib.unified_diff(['\t'.join(row) for row in last_sheet_values], ['\t'.join(row) for row in curr_sheet_values])
    diff_list = list(diff)

    if len(diff_list) > 0:
        worksheet1.update_cell(row, col + 1, f"{current_date} 更新") # 変更があった場合、変更日付付きの通知をマークする

    # 現在のシートの内容を前回のシートにコピー
    last_sheet.clear()
    for i, row in enumerate(curr_sheet_values):
        last_sheet.insert_row(row, i+1)
