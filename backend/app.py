# backend/app.py
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os, pandas as pd, requests, folium, math
from dotenv import load_dotenv
from datetime import datetime

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

def geocode_vworld(address: str):
    addr_type = "road" if is_road_address(address) else "parcel"
    url = "http://api.vworld.kr/req/address"
    params = {
        "service": "address",
        "request": "getcoord",
        "version": "2.0",
        "crs": "EPSG:4326",
        "address": address,
        "format": "json",
        "type": addr_type,
        "key": VWORLD_API_KEY
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        if data["response"]["status"] == "OK":
            point = data["response"]["result"]["point"]
            return float(point["y"]), float(point["x"])
        else:
            return None
    except:
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

    return jsonify({"map_url": f"/map/{filename}"})

@app.route("/map/<path:filename>")
def serve_map(filename):
    return send_from_directory(RESULT_FOLDER, filename)

if __name__ == "__main__":
    app.run(debug=True)
