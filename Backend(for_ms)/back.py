from flask import Flask, jsonify
from flask_cors import CORS # 프론트-유니티 통신을 위해 필수

app = Flask(__name__)
CORS(app) 

# 예시: 분석된 데이터를 전달하는 API
@app.route('/api/data', methods=['GET'])
def get_data():
    # 여기서 파이썬의 분석 로직(Pandas 등)을 실행
    analysis_result = {
        "status": "success",
        "values": [10, 20, 45, 90], # 유니티 그래프용 데이터
        "message": "데이터 분석 완료"
    }
    return jsonify(analysis_result)

if __name__ == '__main__':
    app.run(debug=True, port=5000)