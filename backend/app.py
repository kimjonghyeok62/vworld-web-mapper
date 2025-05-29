# backend/app.py
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os, pandas as pd, requests, folium, math
from dotenv import load_dotenv
from datetime import datetime
import re

app = Flask(__name__)
CORS(app)  # 프론트엔드 요청 허용

load_dotenv()
VWORLD_API_KEY = os.getenv("VWORLD_API_KEY")

UPLOAD_FOLDER = "uploads"
RESULT_FOLDER = "results"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

def is_road_address(address: str) -> bool:
    road_keywords = ("로", "길", "대로", "고가", "순환로")
    return any(token.endswith(road_keywords) for token in address.split())

def clean_address(address: str) -> str:
    """
    주소 문자열을 정제합니다.
    예: "경기 용인시 기흥구 동백로 27, 1502동 703호" → "경기 용인시 기흥구 동백로 27"
    """
    address = re.sub(r'\d{1,4}동\s*\d{1,4}호', '', address)  # "1502동 703호"
    address = re.sub(r'\d{1,4}동', '', address)  # "1502동"
    address = re.sub(r'\d{1,4}호', '', address)  # "703호"
    address = address.strip(', ()')
    return address.strip()

def geocode_vworld(address: str):
    url = "http://api.vworld.kr/req/address"
    cleaned = clean_address(address)

    base_params = {
        "service": "address",
        "request": "getcoord",
        "version": "2.0",
        "crs": "EPSG:4326",
        "address": cleaned,
        "format": "json",
        "key": VWORLD_API_KEY
    }

    for addr_type in ["parcel", "road"]:  # 지번 → 도로명 순서
        params = base_params.copy()
        params["type"] = addr_type

        try:
            response = requests.get(url, params=params)
            data = response.json()

            print(f"[DEBUG] ({addr_type}) 주소 요청: {cleaned}")
            print(f"[DEBUG] 응답 내용: {data}")

            if data["response"]["status"] == "OK":
                point = data["response"]["result"]["point"]
                return float(point["y"]), float(point["x"])
        except Exception as e:
            print(f"[ERROR] 주소 처리 실패: {address} → 예외: {e}")

    print(f"[FAIL] 좌표 찾기 실패: {address}")
    return None

@app.route("/upload", methods=["POST"])
def upload_file():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "파일이 없습니다."}), 400

    df = pd.read_excel(file)
    coord_dict = {}
    for i, row in df.iterrows():
        address = str(row.get("주소")).strip()
        coord = geocode_vworld(address)
        if coord:
            coord_dict[address] = coord

    # 지도 생성
    if not coord_dict:
        return jsonify({"error": "좌표를 찾을 수 없습니다."}), 400

    center = next(iter(coord_dict.values()))
    m = folium.Map(location=center, zoom_start=14)

    for address, coord in coord_dict.items():
        folium.Marker(location=coord, popup=address).add_to(m)

    filename = f"map_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    filepath = os.path.join(RESULT_FOLDER, filename)
    m.save(filepath)

    markers = [
        {"lat": lat, "lng": lng, "tooltip": addr}
        for addr, (lat, lng) in coord_dict.items()
    ]

    return jsonify({
        "map_url": f"/map/{filename}",
        "markers": markers
    })

@app.route("/map/<path:filename>")
def serve_map(filename):
    return send_from_directory(RESULT_FOLDER, filename)

if __name__ == "__main__":
    print("🧪 TEST: VWorld 주소 좌표 변환 테스트")
    print(geocode_vworld("경기 용인시 기흥구 동백중앙로 191"))

    # ✅ 서버 실행 코드 추가
    app.run(host="0.0.0.0", port=5000, debug=True)