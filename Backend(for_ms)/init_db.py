import psycopg2

def init_postgres_db():
    try:
        # ⚠️ password 부분을 본인이 설정한 비밀번호로 꼭 수정하세요!
        conn = psycopg2.connect(
            host="localhost",
            database="postgres", # 기본 생성된 DB를 활용해 에러 방지
            user="postgres",
            password="kuun0727", 
            port="5432"
        )
        cursor = conn.cursor()

        # 1) PostGIS 공간 확장 기능 활성화 (기획서 핵심 기술)
        cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis;")

        # 2) Users 테이블 생성
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                nickname VARCHAR(50) NOT NULL,
                profile_img TEXT
            );
        ''')

        # 3) Posts 테이블 생성 (기획서의 geom 공간 타입 완벽 반영)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                geom GEOMETRY(Point, 4326) NOT NULL,
                place_name VARCHAR(100),
                view_count INTEGER DEFAULT 0,
                board_type VARCHAR(20) DEFAULT '일상',
                category VARCHAR(20) NOT NULL,
                radius_limit DOUBLE PRECISION DEFAULT 300.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        ''')

        # 4) 공간 검색 속도를 위한 GIST 인덱스 생성
        cursor.execute("CREATE INDEX IF NOT EXISTS posts_geom_idx ON posts USING GIST (geom);")

        # 5) Post_Images (1:N) 테이블 생성
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS post_images (
                id SERIAL PRIMARY KEY,
                post_id INTEGER NOT NULL,
                image_url TEXT NOT NULL,
                thumbnail_url TEXT,
                FOREIGN KEY (post_id) REFERENCES posts(id)
            );
        ''')

        # 6) Decorations 테이블 생성
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS decorations (
                id SERIAL PRIMARY KEY,
                post_id INTEGER NOT NULL,
                item_type VARCHAR(50) NOT NULL,
                transform_data TEXT NOT NULL,
                FOREIGN KEY (post_id) REFERENCES posts(id)
            );
        ''')

        # 테스트용 더미 데이터 삽입
        cursor.execute("INSERT INTO users (nickname, profile_img) VALUES ('해커톤마스터', 'https://example.com/user.png') ON CONFLICT DO NOTHING;")
        
        # 기획서 요건: GPS 오차 보정 반경(radius_limit) 필드 포함
        cursor.execute('''
            INSERT INTO posts (user_id, content, geom, place_name, board_type, category, radius_limit)
            VALUES (1, '정문 앞 에어팟 보관 중', ST_SetSRID(ST_MakePoint(127.1484, 35.8115), 4326), '대학교 정문', '일상', '분실물', 300.0);
        ''')

        conn.commit()
        cursor.close()
        conn.close()
        print("🎉 기획서 원본 스택(PostgreSQL + PostGIS) DB 초기화 성공!")

    except Exception as e:
        print(f"❌ DB 연결 실패! 비밀번호를 다시 확인하세요. 에러 내용: {e}")

if __name__ == '__main__':
    init_postgres_db()