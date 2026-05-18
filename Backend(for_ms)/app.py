from flask import Flask, jsonify, request
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

# DB 연결 함수 (아까 성공한 설정 그대로 적용)
def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="postgres",
        user="postgres",
        password="YOUR_PASSWORD",  # ⚠️ 본인의 실제 DB 비밀번호로 수정하세요!
        port="5432"
    )

# 1. 헬스 체크 API (기존 Rust 테스트 함수를 파이썬으로 완벽 대체!)
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "success",
        "message": "파이썬 공간 필터링 엔진 정상 작동 중! 도시 개발 데이터 연동 완료"
    })

# 2. 기획서 핵심 요건: 내 주변 게시글 조회 API (PostGIS 활용)
# 유저의 현재 위도(lat), 경도(lng), 그리고 오차보정 반경(radius, 기본 300m)을 받아 필터링합니다. [cite: 129, 135]
@app.route('/api/posts/nearby', methods=['GET'])
def get_nearby_posts():
    try:
        user_lng = float(request.args.get('lng', 127.1484)) # 기본값: 전북대 정문
        user_lat = float(request.args.get('lat', 35.8115))
        radius = float(request.args.get('radius', 300.0))  # 기획서 반경 설정 오차 보정 [cite: 135, 188]

        conn = get_db_connection()
        # RealDictCursor를 쓰면 딕셔너리 형태로 결과가 나와 jsonify하기 편합니다. 
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # ST_DWithin: PostGIS의 초고속 반경 검색 함수 (GIST 인덱스 적용됨)
        # ST_Distance: 두 지점 간의 실제 거리(m) 계산
        query = """
            SELECT p.id, p.content, p.place_name, p.view_count, p.board_type, p.category,
                   ST_X(p.geom) as lng, ST_Y(p.geom) as lat,
                   ST_Distance(p.geom, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography) as distance
            FROM posts p
            WHERE ST_DWithin(p.geom, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography, %s)
            ORDER BY distance ASC;
        """
        
        cursor.execute(query, (user_lng, user_lat, user_lng, user_lat, radius))
        posts = cursor.fetchall()

        cursor.close()
        conn.close()
        return jsonify({"status": "success", "count": len(posts), "data": posts})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # 플러터(Flutter) 프론트엔드와 통신할 수 있도록 0.0.0.0 포트로 서버 오픈 
    app.run(host='0.0.0.0', port=5000, debug=True)