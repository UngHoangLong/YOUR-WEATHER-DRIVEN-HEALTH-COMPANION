import { useState } from 'react';
import type { FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify'; // Đảm bảo bạn đã cài đặt react-toastify
import './Register.css';

function Register() {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'ngrok-skip-browser-warning': 'true',
        },
        body: JSON.stringify({ username, email, password }),
      });

      const data = await response.json();

      if (response.ok) {
        // Đăng ký thành công
        toast.success('Đăng ký thành công! Bạn sẽ được chuyển hướng.', {
          position: "top-right",
          autoClose: 1000,
          onClose: () => navigate('/login'), // Chuyển hướng sau khi thông báo đóng
        });
      } else {
        // Xử lý lỗi từ server (trùng username/email)
        toast.error(data.detail || 'Đăng ký thất bại. Vui lòng thử lại.');
      }
    } catch (error) {
      // Xử lý lỗi khi không kết nối được đến server
      toast.error('Không thể kết nối đến máy chủ. Vui lòng thử lại sau.');
    } finally {
      setIsLoading(false); // Kết thúc loading bất kể thành công hay thất bại
    }
  };

  return (
    <div className="login-page-container">
      {/* Phần bên trái: Hình ảnh và slogan */}
      <div className="visual-section">
        <h1 className="slogan-title">Your Weather-Driven Health Companion.</h1>
      </div>

      {/* Phần bên phải: Form đăng ký */}
      <div className="login-form-container">
        <div className="login-card-register">
          <h1 className="logo-text">HealthTwin</h1>
          <h2 className="register-text-title">Đăng ký để khám phá những tính năng độc đáo.</h2>
          <form className="form" onSubmit={handleSubmit}>
            <input
              type="text"
              placeholder="Tên người dùng"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="input-field dark-input"
            />
            <input
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="input-field dark-input"
            />
            <input
              type="password"
              placeholder="Mật khẩu"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input-field dark-input"
            />
            <button type="submit" className="form-button primary-button" disabled={isLoading}>
              {isLoading ? 'Đang đăng ký...' : 'Đăng ký'}
            </button>
          <div className="divider">
            <span>Hoặc</span>
          </div>
          {/* Link chuyển về trang đăng nhập */}
          <Link to="/login" className="form-link">Đã có tài khoản? Đăng nhập</Link>
          </form>
        </div>
      </div>
    </div>
  );
}

export default Register;