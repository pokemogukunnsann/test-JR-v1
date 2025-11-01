import subprocess
import json
from flask import Flask, request, jsonify, abort
# 標準ライブラリのurllib.parseからquoteをインポート
from urllib.parse import quote 
print(f"urllib.parse.quote: {quote}")

# Flaskアプリケーションの初期化
app = Flask(__name__)
print(f"app:{app}")

# 外部APIのベースURL
API_BASE_URL = "https://unchinkensaku.jre-maas.com/v1/json/search/course/extreme"
EXTERNAL_API_ENCODING = 'shift_jis'
print(f"API_BASE_URL:{API_BASE_URL}")
print(f"EXTERNAL_API_ENCODING:{EXTERNAL_API_ENCODING}")

@app.route('/fare', methods=['GET'])
def get_fare():
    print(f"\n--- API Call Received ---")
    
    start_station = request.args.get('station')
    print(f"start_station:{start_station}")
    end_station = request.args.get('to')
    print(f"end_station:{end_station}")
    
    if not start_station or not end_station:
        return jsonify({"error": "乗車駅(station)と降車駅(to)を指定してください"}), 400

    # ★ 改善点: 日本語駅名をURLセーフな形式にエンコード ★
    # 日本語はデフォルトでUTF-8でエンコードされます
    encoded_start = quote(start_station)
    print(f"encoded_start: {encoded_start}")
    encoded_end = quote(end_station)
    print(f"encoded_end: {encoded_end}")
    
    via_list = f"{encoded_start}:{encoded_end}"
    print(f"via_list (encoded): {via_list}")
    
    external_url = (
        f"{API_BASE_URL}?"
        f"viaList={via_list}&"
        f"date=20260410&"
        f"teikiKind=bussiness&"
        f"mode=fare"
    )
    print(f"External API URL:{external_url}")

    # cURLコマンドの実行とデコード (前回と同じロジック)
    # ... (subprocess.run() を使った cURL 実行ロジックは省略) ...
    curl_command = ["curl", "-s", "-L", external_url] 
    
    try:
        # ... (cURL実行: result = subprocess.run(...) ) ...
        # サンプルのため、ここでは cURL の実行結果を模擬します
        # 実際には上記の subprocess.run を使用してください
        
        # --- cURL実行の模擬スタート ---
        import time; time.sleep(0.1) # 実行待ちを模擬
        # ここでは成功した Shift_JIS バイト列を模擬 (実際のJR APIからのレスポンスを想定)
        mock_shift_jis_content = b'{"ResultSet":{"Course":[{"Price":[{"Oneway":"210"},{"Oneway":"209"}],"Route":{"Point":[{"Station":{"Name":"\x93\x8c\x8b\x9e"}},{"Station":{"Name":"\x95\xdb\x9cb"}}]}...}]}}'
        binary_content = mock_shift_jis_content 
        # --- cURL実行の模擬エンド ---
        
        print(f"Partial Binary Content (100 bytes): {binary_content[:100]}...")

        decoded_text = binary_content.decode(EXTERNAL_API_ENCODING)
        print(f"Attempted decode with {EXTERNAL_API_ENCODING}.")

        parsed_json = json.loads(decoded_text)
        print(f"✅ JSON successfully parsed.")

        # クリーンなUTF-8 JSONをFlaskクライアントに返す
        return jsonify(parsed_json)

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        return jsonify({"error": "処理中にエラーが発生しました", "details": str(e)}), 500
    finally:
        print(f"--- API Call End ---")

# アプリケーションの実行
if __name__ == '__main__':
    # Flask実行時には cURL は実行環境にインストールされている必要があります
    app.run(debug=True)
