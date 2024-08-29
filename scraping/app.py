from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import dropbox
import base64
import requests
from datetime import datetime
import logging
from logging import StreamHandler, FileHandler, Formatter
from logging import INFO, DEBUG, NOTSET

# ストリームハンドラの設定
stream_handler = StreamHandler()
stream_handler.setLevel(INFO)
stream_handler.setFormatter(Formatter("%(message)s"))

# 保存先の有無チェック
if not os.path.isdir('./Log'):
    os.makedirs('./Log', exist_ok=True)

# ファイルハンドラの設定
file_handler = FileHandler(
    f"./Log/buss_time_table_download_log{datetime.now():%Y%m%d%H%M%S}.log"
)
file_handler.setLevel(DEBUG)
file_handler.setFormatter(
    Formatter(
        "%(asctime)s@ %(name)s [%(levelname)s] %(message)s")
)

# ルートロガーの設定
logging.basicConfig(level=NOTSET, handlers=[stream_handler, file_handler])
logger = logging.getLogger(__name__)

# ホームディレクトリのパスを取得
# home_directory = os.path.expanduser("~")

# このスクリプトが置かれているディレクトリのパスを取得
current_directory = os.path.dirname(os.path.abspath(__file__))
# スクリプトが置かれているディレクトリの一つ上の階層のパスを取得
parent_directory = os.path.dirname(current_directory)
# ダウンロード先のディレクトリ名を指定
download_directory_name = "buss_schedule"
# ディレクトリを作成
download_directory_path = os.path.join(
    parent_directory, download_directory_name)
os.makedirs(download_directory_path, exist_ok=True)

# pdfをダウンロードできるようにするオプション
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_experimental_option("prefs", {
    "download.default_directory": download_directory_path,
    "plugins.always_open_pdf_externally": True
})

try:
    # pdfのオプション付きでChromeを立ち上げる
    driver = webdriver.Chrome(options=options)
    portal_url = 'https://www.chitose.ac.jp/info/access'
    driver.get(portal_url)

# ログインに必要な情報
# my_user_ID = os.getenv('MY_STUDENT_NUMBER')
# my_password = os.getenv('MY_UNIV_PORTAL_PASS')
#
# ログインする箇所を特定
# input_user_ID = driver.find_element(By.XPATH, "//input[@id='userID']")
# input_password = driver.find_element(By.XPATH, "//input[@id='password']")
# submit_button = driver.find_element(
#    By.XPATH, '/html/body/div/div[3]/form/div[3]/div/input')
#
# 入力フォームに入力する
# input_user_ID.send_keys(my_user_ID)
# input_password.send_keys(my_password)
#
# time.sleep(2)
#
# submit_button.click()
#
# time.sleep(2)
#
# rennraku_link = driver.find_element(By.XPATH, "//a[contains(text(),'連絡')]")
# rennraku_link.click()
#
# time.sleep(2)
#
# midoku_top_link = driver.find_element(By.XPATH, "//tbody/tr[2]/td[4]/a[1]")
# midoku_top_link.click()
#
# time.sleep(2)

    element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
        (By.XPATH, '/html/body/div[1]/div[1]/div[2]/div/div[2]/div/div/div/div[6]/div/div/div[3]/a')))
    pdf_url = element.get_attribute('href')

    response = requests.get(pdf_url)

    # 現在の時刻を使ってファイル名を作成
    current_time = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"downloaded_{current_time}.pdf"
    file_path = os.path.join(download_directory_path, filename)

    # ファイルを保存
    with open(file_path, 'wb') as file:
        file.write(response.content)
    logger.info("Successfully downloaded")

# buss_sche_pdf_link = driver.find_element(
#    By.CSS_SELECTOR, "div.wrapper div.mainBody:nth-child(3) div.container-fluid div.row-fluid div.span9.w95p_print div.content div.panel_bottom_bg div.panel.details div.panelBody.simple table.orig td.orig.vtop:nth-child(2) div.OfficememoContent:nth-child(5) ul:nth-child(3) li:nth-child(1) > a:nth-child(1)")
# buss_sche_pdf_link.click()

finally:
    driver.quit()

# ディレクトリ内のファイル一覧を取得
pdfs = [f for f in os.listdir(download_directory_path) if os.path.isfile(
    os.path.join(download_directory_path, f))]

# ファイルの更新日時を比較して最新のファイルを見つける
latest_pdf_name = max(pdfs, key=lambda x: os.path.getctime(
    os.path.join(download_directory_path, x)))

# print("Downloaded PDF is ", latest_pdf_name)
logger.info("latest PDF is : %s", latest_pdf_name)

# アプリのクライアントIDとクライアントシークレット
app_key = os.getenv("APP_KEY")
app_secret = os.getenv("APP_SECRET")

# リフレッシュトークン
refresh_token = os.getenv("REFRESH_TOKEN")

# OAuth 2.0のトークンリフレッシュエンドポイント
token_refresh_url = 'https://api.dropbox.com/oauth2/token'

# リクエストボディ
data = {
    'grant_type': 'refresh_token',
    'refresh_token': refresh_token,
}

# 認証情報をヘッダーに設定
headers = {
    'Authorization': f'Basic {base64.b64encode(f"{app_key}:{app_secret}".encode()).decode()}'
}

# POSTリクエストを送信
response = requests.post(token_refresh_url, data=data, headers=headers)

# レスポンスを表示
# print("Got json is ", response.json())

# レスポンスからaccess_tokenを取得
response_data = response.json()
access_token = response_data.get('access_token')

# レスポンスを表示
logger.info('Got json is : %s', str(response_data))

# if access_token:
#    # access_tokenを環境変数にエクスポート
#    os.environ['DROPBOX_TOKEN'] = access_token
#    print(f'DROPBOX_TOKEN 環境変数にセットしました: {access_token}')
# else:
#    print('access_tokenが見つかりません。')

dbx = dropbox.Dropbox(access_token)
dbx.users_get_current_account()

f = open(download_directory_path + '/' + latest_pdf_name, 'rb')
dbx.files_upload(f.read(), '/buss_schedule/' + latest_pdf_name)
f.close()
