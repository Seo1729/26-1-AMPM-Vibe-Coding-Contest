from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import sys

sys.path.append('./geo_engine')
import geo_engine

app = Flask(__name__)
CORS(app)

def get_db_connection():
    conn = sqlite3.connect('local_board.db')
    conn.row_factory = sqlite3.Row
    return conn

# [기획서 기능 4.1] 게시글 작성 API [cite: 18]
@app.route('/api/posts', methods=['POST'])
def create_post():
    data = request.json
    user_id = data.get('user_id')
    content = data.get('content') [cite: 46]
    latitude = float(data.get('latitude')) [cite: 47]
    longitude = float(data.get('longitude')) [cite: 47]
    place_name = data.get('place_name', '') [cite: 48]
    board_type = data.get('board_type', '일상') [cite: 83]
    category = data.get('category', '일상') [cite: 31]
    radius_limit = float(data.get('radius_limit', 300.0)) [cite: 88] # 위치 보정 범위 [cite: 86]

    # 이미지 및 꾸미기 데이터 (Optional) [cite: 30, 56]
    image_url = data.get('image_url') [cite: 54]
    thumbnail_url = data.get('thumbnail_url') [cite: 55]

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Posts 테이블 저장 [cite: 43]
    cursor.execute('''
        INSERT INTO posts (user_id, content, latitude, longitude, place_name, board_type, category, radius_limit)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, content, latitude, longitude, place_name, board_type, category, radius_limit))
    post_id = cursor.lastrowid

    # 2. 이미지 정보가 있으면 Post_Images에 저장 [cite: 50]
    if image_url:
        cursor.execute('''
            INSERT INTO post_images (post_id, image_url, thumbnail_url)
            VALUES (?, ?, ?)
        ''', (post_id, image_url, thumbnail_url))

    conn.commit()
    conn.close()

    return jsonify({"status": "success", "post_id": post_id}), 201


# [기획서 기능 4.1 & 4.2] 내 주변 게시글 목록 조회 API (Rust 필터링 도입) [cite: 19, 28]
@app.route('/api/posts/nearby', methods=['POST'])
def get_nearby_posts():
    data = request.json
    user_lat = float(data.get('latitude'))
    user_lng = float(data.get('longitude'))
    selected_board = data.get('board_type', '일상') # 일상게시판 / 비밀게시판 필터 
    selected_category = data.get('category') # 카테고리 필터 (선택 사항) 
    sort_by = data.get('sort_by', 'latest') # 'latest'(최신순) 또는 'popular'(인기순) 

    conn = get_db_connection()
    
    # 쿼리 기본 빌드
    query = "SELECT p.*, u.nickname FROM posts p JOIN users u ON p.user_id = u.id WHERE p.board_type = ?"
    params = [selected_board]

    if selected_category:
        query += " AND p.category = ?"
        params.append(selected_category)

    # 기획서 요건: 인기 게시글 / 최신 게시글 정렬 
    if sort_by == 'popular':
        query += " ORDER BY p.view_count DESC" [cite: 49]
    else:
        query += " ORDER BY p.created_at DESC"

    posts = conn.execute(query, params).fetchall()
    conn.close()

    if not posts:
        return jsonify([])

    # Rust 엔진 연산을 위한 원시 배열 가공
    lats = [row['latitude'] for row in posts]
    lngs = [row['longitude'] for row in posts]
    limits = [row['radius_limit'] for row in posts]

    # Rust 고속 엔진 호출하여 내 주변 노출 범위 필터링 
    render_flags = geo_engine.filter_local_posts(user_lat, user_lng, lats, lngs, limits)

    response_data = []
    for i, row in enumerate(posts):
        if render_flags[i] == 1: # Rust가 노출 가능하다고 판단한 게시글만 조립 
            response_data.append({
                "id": row['id'],
                "nickname": row['nickname'],
                "content": row['content'],
                "latitude": row['latitude'],
                "longitude": row['longitude'],
                "place_name": row['place_name'],
                "view_count": row['view_count'],
                "category": row['category'],
                "board_type": row['board_type']
            })

    return jsonify(response_data)


# [기획서 기능 10] 상세 페이지 접속 시 view_count 올리는 로직 반영 API 
@app.route('/api/posts/<int:post_id>', methods=['GET'])
def get_post_detail(post_id):
    conn = get_db_connection()
    
    # 1. 기획서 명시: 상세 페이지 진입 시 조회수 증가 
    conn.execute('UPDATE posts SET view_count = view_count + 1 WHERE id = ?', (post_id,))
    conn.commit()

    # 2. 게시글 상세 및 유저 닉네임 가져오기 [cite: 41, 43]
    post = conn.execute('''
        SELECT p.*, u.nickname, u.profile_img 
        FROM posts p JOIN users u ON p.user_id = u.id 
        WHERE p.id = ?
    ''', (post_id,)).fetchone()

    if post is None:
        conn.close()
        return jsonify({"error": "Post not found"}), 404

    # 3. 이미지 정보(1:N) 및 꾸미기 요소 가져오기 [cite: 50, 56]
    images = conn.execute('SELECT image_url, thumbnail_url FROM post_images WHERE post_id = ?', (post_id,)).fetchall()
    decorations = conn.execute('SELECT item_type, transform_data FROM decorations WHERE post_id = ?', (post_id,)).fetchall()
    conn.close()

    return jsonify({
        "id": post['id'],
        "nickname": post['nickname'],
        "profile_img": post['profile_img'],
        "content": post['content'],
        "place_name": post['place_name'],
        "view_count": post['view_count'] + 1, # 업데이트된 값 반영
        "category": post['category'],
        "board_type": post['board_type'],
        "images": [{"image_url": img['image_url'], "thumbnail_url": img['thumbnail_url']} for img in images],
        "decorations": [{"item_type": d['item_type'], "transform_data": d['transform_data']} for d in decorations]
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)