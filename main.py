import subprocess
import json
from flask import Flask, request, jsonify, abort
from urllib.parse import quote
from json.decoder import JSONDecodeError 
print(f"Flask:{Flask}, subprocess:{subprocess}, json:{json}, quote:{quote}, JSONDecodeError:{JSONDecodeError}")

# Flaskアプリケーションの初期化
app = Flask(__name__)
print(f"app:{app}")

# 外部APIのベースURL
API_BASE_URL = "https://unchinkensaku.jre-maas.com/v1/json/search/course/extreme"
print(f"API_BASE_URL:{API_BASE_URL}")

# ★ 修正点: 試行するエンコーディングのリスト (Shift JIS系を最優先)
CANDIDATE_ENCODINGS = ['shift_jis', 'eucJP-win', 'utf-8']
print(f"CANDIDATE_ENCODINGS:{CANDIDATE_ENCODINGS}")

@app.route('/fare', methods=['GET'])
def get_fare():
    print(f"\n--- API Call Received ---")
    
    start_station = request.args.get('station')
    print(f"start_station:{start_station}")
    end_station = request.args.get('to')
    print(f"end_station:{end_station}")
    
    # 必須パラメータのチェック
    if not start_station or not end_station:
        print("❌ Missing required parameters: station or to.")
        return jsonify({"error": "乗車駅(station)と降車駅(to)を指定してください"}), 400

    # 日本語駅名をURLセーフな形式にエンコード（UTF-8エンコード）
    encoded_start = quote(start_station)
    print(f"encoded_start: {encoded_start}")
    encoded_end = quote(end_station)
    print(f"encoded_end: {encoded_end}")
    
    # 経由リストを作成 (今回は直行ルート)
    via_list = f"{encoded_start}:{encoded_end}"
    print(f"via_list (encoded): {via_list}")
    
    # 外部APIの完全なURLを構築
    external_url = (
        f"{API_BASE_URL}?"
        f"viaList={via_list}&"
        f"date=20260410&"
        f"teikiKind=bussiness&"
        f"mode=fare"
    )
    print(f"External API URL:{external_url}")

    # cURLコマンドの実行
    curl_command = ["curl", "-s", "-L", external_url] 
    
    try:
        # cURLを実行し、バイナリレスポンスを取得
        result = subprocess.run(
            curl_command, 
            capture_output=True, 
            check=True, # 0以外のリターンコードの場合、CalledProcessErrorを発生させる
            shell=False
        )
        binary_content = result.stdout
        print(f"cURL returncode: {result.returncode}")
        print(f"Partial Binary Content (100 bytes): {binary_content[:100]}...")

        parsed_json = None
        last_error = None
        
        # ★ 修正箇所: 候補エンコーディングを順番に試すフォールバックロジック ★
        for encoding in CANDIDATE_ENCODINGS:
            print(f"\nAttempting decode and parse with encoding: {encoding}...")
            
            try:
                # デコードエラーは無視（errors='ignore'）し、JSON構文の破壊を防ぐ
                decoded_text = binary_content.decode(encoding, errors='ignore') 
                print(f"Decoded text length: {len(decoded_text)}")
                
                # JSONとしてパースを試みる
                parsed_json = json.loads(decoded_text)
                
                print(f"✅ Success! Parsed with {encoding}.")
                # 成功した時点でループを抜ける
                break 

            except (UnicodeDecodeError, JSONDecodeError) as e:
                # デコードまたはJSONパースに失敗した場合、次のエンコーディングを試す
                print(f"❌ Failed with {encoding}. Error: {type(e).__name__}")
                last_error = e
                continue 

        # 全てのデコーディングを試行後に結果をチェック
        if parsed_json is not None:
            # 成功した場合、JSONを返す
            return jsonify(parsed_json)
        else:
            # 全て失敗した場合、エラーを返す
            print(f"❌ All decoding attempts failed.")
            return jsonify({
                "error": "外部APIのレスポンスを解析できませんでした", 
                "details": f"最終エラー: {type(last_error).__name__} - {str(last_error)}",
                "attempted_encodings": CANDIDATE_ENCODINGS
            }), 500

    except subprocess.CalledProcessError as e:
        print(f"❌ cURL実行エラー (Return Code {e.returncode})")
        # cURLのエラー出力をデコードして返す
        return jsonify({"error": "外部APIの呼び出しに失敗しました", "details": e.stderr.decode('utf-8', errors='ignore')}), 503
    except Exception as e:
        print(f"❌ 予期せぬエラーが発生しました: {e}")
        return jsonify({"error": "プロキシ処理中に予期せぬエラーが発生しました", "details": str(e)}), 500
    finally:
        print(f"--- API Call End ---")

# アプリケーションの実行 (デバッグモードを有効に)
if __name__ == '__main__':
    app.run(debug=True)
