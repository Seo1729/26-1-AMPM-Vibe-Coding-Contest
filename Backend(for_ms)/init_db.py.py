import sqlite3

def init_original_db():
    conn = sqlite3.connect('local_board.db')
    cursor = conn.cursor()

    # 1) Users (사용자) 테이블 [cite: 39]
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, -- 고유 식별자 [cite: 40]
            nickname TEXT NOT NULL,               -- 서비스 내 별명 [cite: 41]
            profile_img TEXT                      -- 프로필 이미지 URL [cite: 42]
        )
    ''')

    # 2) Posts (지도 게시글) 테이블 [cite: 43]
    # 기획서의 geom(Geometry) 대신 SQLite 환경에 맞춰 latitude, longitude로 분ining하되 [cite: 47]
    # 카테고리, 게시판종류 필드를 원본 그대로 추가합니다.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,  -- 고유 식별자 [cite: 44]
            user_id INTEGER NOT NULL,              -- 작성자 식별자 [cite: 45]
            content TEXT NOT NULL,                 -- 게시글 텍스트 [cite: 46]
            latitude REAL NOT NULL,                -- 위도 (geom 대용) [cite: 47]
            longitude REAL NOT NULL,               -- 경도 (geom 대용) [cite: 47]
            place_name TEXT,                       -- 장소 이름 (지도 라벨용) [cite: 48]
            view_count INTEGER DEFAULT 0,          -- 조회수 [cite: 49]
            board_type TEXT DEFAULT '일상',        -- 일상게시판 / 비밀게시판 구분 
            category TEXT NOT NULL,                -- 일상/질문/정보/분실물/거래 
            radius_limit REAL DEFAULT 300.0,       -- 위치 보정 범위 설정 (100m~500m) [cite: 34, 88]
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # 3) Post_Images (게시글 사진 - 1:N 관계) 테이블 [cite: 50]
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS post_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT, -- 고유 식별자 [cite: 52]
            post_id INTEGER NOT NULL,             -- 연결된 게시글 ID [cite: 53]
            image_url TEXT NOT NULL,              -- S3 등 원본 이미지 주소 [cite: 54]
            thumbnail_url TEXT,                   -- 지도 마커용 작은 이미지 주소 [cite: 55]
            FOREIGN KEY (post_id) REFERENCES posts(id)
        )
    ''')

    # 4) Decorations (장소 꾸미기 요소) 테이블 [cite: 56]
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS decorations (
            id INTEGER PRIMARY KEY AUTOINCREMENT, -- 고유 식별자 [cite: 57]
            post_id INTEGER NOT NULL,             -- 꾸미기가 적용된 게시글 [cite: 58]
            item_type TEXT NOT NULL,              -- 스티커, 효과 등 종류 [cite: 59]
            transform_data TEXT NOT NULL,         -- 위치, 회전, 크기 값 (JSON 형식) [cite: 60]
            FOREIGN KEY (post_id) REFERENCES posts(id)
        )
    ''')

    # 데모 가짜 데이터 삽입 (테스트용)
    cursor.execute("INSERT INTO users (nickname, profile_img) VALUES ('해커톤초보', 'https://example.com/user1.png')")
    cursor.execute('''
        INSERT INTO posts (user_id, content, latitude, longitude, place_name, board_type, category, radius_limit)
        VALUES (1, '정문 앞에 에어팟 프로 분실하신 분? 매점에 맡겨둡니다.', 35.8115, 127.1484, '대학교 정문', '일상', '분실물', 200.0)
    ''')
    cursor.execute("INSERT INTO post_images (post_id, image_url, thumbnail_url) VALUES (1, 'https://img.com/airpods.jpg', 'https://img.com/thumb_airpods.jpg')")
    cursor.execute("INSERT INTO decorations (post_id, item_type, transform_data) VALUES (1, 'sticker', '{\"x\": 50, \"y\": 50, \"scale\": 1.0}')")

    conn.commit()
    conn.close()
    print("기획서 원본 기준 데이터베이스(local_board.db) 생성 완료!")

if __name__ == '__main__':
    init_original_db()