# 使用ライブラリ
import difflib
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz

# 認証情報
from google.oauth2.service_account import Credentials
import gspread

scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

#認証キーのファイルパスを""に入力

credentials = Credentials.from_service_account_file(
    "",
    scopes=scopes
)

gc = gspread.authorize(credentials)

# スプレッドシートURLを""に入力。

spreadsheet_url = "" 

spreadsheet = gc.open_by_url(spreadsheet_url)
worksheet1 = spreadsheet.get_worksheet(0)  # Sheet1

# スプレッドシートURLを入力。

url_col = 2  # B列 URLリスト
tag_class_col = 8 #H列 抽出タグ情報


# ワークシート1の列Bを順番に処理
last_row = len(worksheet1.col_values(url_col)) #URLリストの総数を数える。
for row in range(2, last_row + 1): #URLリストの総数+1繰り返す。
    print(f"Processing row {row} of {last_row}") #デバッグ用出力
    
    url = worksheet1.cell(row, url_col).value # スプレットシートのURLを取得   
    print(url) #デバッグ用出力

    tags_classes_str = worksheet1.cell(row, tag_class_col).value

    print(f"Before conversion, tags_classes_str: {tags_classes_str}")  # デバッグ用出力

    tags_classes = []
    if tags_classes_str is not None:
        tags_classes = [tuple(tag_class.split(",")) for tag_class in tags_classes_str.split(".")] 
    print(f"After conversion, tags_classes: {tags_classes}")  # デバッグ用出力

    if url is None or url == "":
        print("end")
        break #break文を削除してもプログラムは動作します


    # 前回差分比較用にlast_sheet(URLリストNo.)でシートを作成。

    last_sheet_title = f"LastSheet{row}"

    last_sheet = None
    curr_sheet = None

    for sheet in spreadsheet.worksheets():
        if sheet.title == last_sheet_title:
            last_sheet = sheet

    if last_sheet is None:
        last_sheet = spreadsheet.add_worksheet(title=last_sheet_title, rows="100", cols="20")


    #ページのHMTLを取得。できなかった場合、エラー処理をする。
    try:
        response = requests.get(url)
    except requests.exceptions.RequestException as e:  # すべてのrequestsエラーを捕捉
        worksheet1.update_cell(row, url_col + 1, f"エラー: {e}")
        continue

    soup = BeautifulSoup(response.content, 'html.parser', from_encoding='utf-8')  # 取得したHTMLを解析


    #配列の中身をクリア

    tags_text = []
    elements =[]
    tag = ""
    class_ = ""
    tag_class = ""

    #tag_classをtagとclassに分ける。リストの中が一つの場合tagのみ

    for tag_class in tags_classes:
        if len(tag_class) == 2:
            tag, class_ = tag_class
            elements = soup.find_all(tag, class_=class_)
        elif len(tag_class) == 1:
            tag = tag_class[0]
            elements = soup.find_all(tag)
        else:
            print(f"Invalid tag_class: {tag_class}")
            continue

    print(f"Found {len(elements)} elements for tag={tag}, class_={class_ if len(tag_class) == 2 else 'N/A'}")  # 各タグとクラスに対する要素の数を出力

     #tagとclassの情報に基づいて、テキストを抽出

    for element in elements:
        tags_text.append(element.get_text(strip=True))

    else:
        print(f"Extracted text: {tags_text}")  #デバッグ用出力

       #tags_textが空の場合（抽出したテキストがない場合）全文抽出する。

    try:
        if tags_text == []:
            print("get all text") #デバッグ用出力
            entire_page_text = soup.get_text()

        else:
            curr_sheet = (tags_text)  #tag_textの内容をcurr_sheetに入力する

    except gspread.exceptions.APIError as e:  #書き込みエラーを捕捉
        worksheet1.update_cell(row, url_col + 1, f"エラー: {e}")
        continue

    if curr_sheet is None:
        curr_sheet_values = entire_page_text # 全文検出の時は改行しない

    else:
        curr_sheet_values = '\n'.join(curr_sheet) #タグ抽出の場合、改行をしてスプレットシート内のデータと状態を揃える。

    last_sheet_values = last_sheet.cell(1, 1).value or "" #前回時差分のテキストデータ取得

    diff = difflib.unified_diff([last_sheet_values], [curr_sheet_values]) #差分検出
    diff_list = list(diff) #差分検出数をリスト型で取得
    print("diff_list",len(diff_list)) #diff_listの数字を出力。デバッグ用

    # 現在の日付を取得
    #current_date = datetime.now(pytz.timezone('Asia/Tokyo')).strftime('%Y-%m-%d')
    current_date = datetime.now(pytz.timezone('Asia/Tokyo')).strftime('%Y-%m-%d,%H:%M') #デバッグ用に時間まで表示させています。

    if len(diff_list) > 0:
        worksheet1.update_cell(row, url_col + 1, f"{current_date} 更新") # 変更があった場合、変更日付付きの通知をマークする

    # 現在のシートの内容を前回のシートにコピー

    last_sheet.clear() #前回時シートの中身をクリア
    last_sheet.update_cell(1, 1, str(curr_sheet_values)) #今回時更新テキストを前回更新シートに書き込み
