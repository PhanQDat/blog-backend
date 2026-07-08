import os
import time
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def get_db_connection():
    """Hàm kết nối tới Postgres có cơ chế tự động thử lại"""
    retries = 5
    while retries > 0:
        try:
            conn = psycopg2.connect(
                host=os.environ.get('DB_HOST', 'postgres-db'),
                database=os.environ.get('DB_NAME', 'blog_db'),
                user=os.environ.get('DB_USER', 'myuser'),
                password=os.environ.get('DB_PASSWORD', 'mypassword'),
                cursor_factory=RealDictCursor
            )
            return conn
        except psycopg2.OperationalError:
            retries -= 1
            print(f"⚠️ Chưa kết nối được tới Database. Thử lại sau 2 giây... (Còn {retries} lần thử)")
            time.sleep(2)
            
    raise Exception("❌ Thất bại: Không thể kết nối tới Database sau nhiều lần thử lại!")

def init_db():
    """Khởi tạo bảng bằng CURSOR của Postgres"""
    conn = get_db_connection()
    with conn.cursor() as cur:
        # Tạo bảng nếu chưa tồn tại
        cur.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Kiểm tra xem database có trống không
        cur.execute('SELECT COUNT(*) FROM posts')
        if cur.fetchone()['count'] == 0:
            cur.execute("INSERT INTO posts (title, content) VALUES (%s, %s)",
                        ('Bài viết mẫu Postgres', 'Chào mừng bạn đến với blog chạy bằng 3 Docker Container tách biệt!'))
            
    conn.commit()
    conn.close()

# --- ROUTES API ---

@app.route('/api/posts', methods=['GET'])
def get_posts():
    """API lấy toàn bộ bài viết"""
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute('SELECT * FROM posts ORDER BY created DESC')
        posts = cur.fetchall()
    conn.close()
    
    # Do dùng RealDictCursor nên posts đã là danh sách các dict chuẩn JSON
    return jsonify(posts)

@app.route('/api/posts', methods=['POST'])
def create_post():
    """API tạo bài viết mới"""
    data = request.json
    title = data.get('title')
    content = data.get('content')

    if not title or not content:
        return jsonify({'error': 'Vui lòng điền đủ thông tin'}), 400

    conn = get_db_connection()
    with conn.cursor() as cur:
        # Postgres dùng ký hiệu %s thay vì dấu hỏi chấm (?) của SQLite
        cur.execute('INSERT INTO posts (title, content) VALUES (%s, %s)', (title, content))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Tạo bài viết thành công!'}), 201

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)