import os
import tempfile
import pytest
from app import app, get_db_connection

@pytest.fixture
def client():
    """Fixture tạo file database tạm thời biệt lập cho từng bài test"""
    # Tạo một file tạm thời trên ổ đĩa cứng
    db_fd, db_path = tempfile.mkstemp()
    
    # Cấu hình Flask sử dụng file tạm này làm database
    app.config['DATABASE'] = db_path
    app.config['TESTING'] = True

    # Khởi tạo cấu trúc bảng sạch trên file tạm vừa tạo
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

    # Trả về test client để tiến hành chạy các hàm test
    with app.test_client() as client:
        yield client

    # Sau khi bài test chạy xong, đóng file và xóa file tạm để giải phóng ổ đĩa
    os.close(db_fd)
    os.unlink(db_path)

# --- CÁC BÀI TEST CHỨC NĂNG ---

def test_get_posts_empty(client):
    """Test 1: File database tạm mới sinh ra chắc chắn phải trống"""
    response = client.get('/api/posts')
    assert response.status_code == 200
    assert response.is_json
    assert len(response.get_json()) == 0

def test_create_post(client):
    """Test 2: Kiểm tra chức năng tạo bài viết mới"""
    payload = {
        "title": "Bài viết Test Chức Năng",
        "content": "Nội dung này được tạo tự động bởi pytest."
    }
    response = client.post('/api/posts', json=payload)
    assert response.status_code == 201
    assert response.get_json()['message'] == 'Tạo bài viết thành công!'

def test_get_posts_after_creation(client):
    """Test 3: Tạo xong và lấy danh sách về kiểm tra phần tử mới nhất"""
    # Chèn một bài viết vào database sạch
    client.post('/api/posts', json={"title": "Blog Docker", "content": "Hello"})
    
    response = client.get('/api/posts')
    data = response.get_json()
    
    assert len(data) == 1
    assert data[0]['title'] == "Blog Docker"
    assert data[0]['content'] == "Hello"

def test_create_post_missing_data(client):
    """Test 4: Kiểm tra tính năng chặn dữ liệu thiếu (Validation)"""
    payload = {"title": "Thiếu nội dung"}
    response = client.post('/api/posts', json=payload)
    assert response.status_code == 400
    assert 'error' in response.get_json()