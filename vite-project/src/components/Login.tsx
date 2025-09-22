// src/components/Login.tsx
import { useState } from 'react';
import type { FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import './Form.css';

function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent) => { // Sửa lỗi bằng cách thêm kiểu FormEvent
    e.preventDefault();

    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'ngrok-skip-browser-warning': 'true',
        },
        body: JSON.stringify({ username, password }),
      });
      const data = await response.json();

      if (response.ok) {
        // Lưu access_token và user_name vào sessionStorage
        sessionStorage.setItem('access_token', data.access_token);
        sessionStorage.setItem('username', username); // giúp chuyển hướng cho tài khoản mới đăng nhập
        
        // Kiểm tra xem người dùng đã từng thiết lập thông tin chưa
        const isSetup = localStorage.getItem(`is_setup_${username}`);
        const redirectTo = isSetup ? '/dashboard' : '/setup';

        toast.success('Đăng nhập thành công!', {
          position: "top-right",
          autoClose: 1500,
          hideProgressBar: false,
          closeOnClick: true,
          pauseOnHover: true,
          draggable: true,
          progress: undefined,
          onClose: () => navigate(redirectTo), // Chuyển hướng đến trang phù hợp
        });
      } else {
        toast.error(data.detail || 'Đăng nhập thất bại.');
      }
    } catch (error) {
      toast.error('Không thể kết nối đến máy chủ. Vui lòng thử lại sau.');
    }
  };

  return (
    <div className="login-page-container">
      <div className="visual-section">
        <h1 className="slogan-title">Your Weather-Driven Health Companion.</h1>
      </div>
      <div className="login-form-container">
        <div className="login-card">
          <h1 className="logo-text">HealthTwin</h1>
          <form className="form" onSubmit={handleSubmit}>
            <input
              type="text"
              placeholder="Tên người dùng"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="input-field dark-input"
            />
            <input
              type="password"
              placeholder="Mật khẩu"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input-field dark-input"
            />
            <button type="submit" className="form-button primary-button">Đăng nhập</button>
            <div className="divider">
              <span>Hoặc</span>
            </div>
            <Link to="/register" className="form-link">Tạo tài khoản mới</Link>
          </form>
        </div>
      </div>
    </div>
  );
}

export default Login;