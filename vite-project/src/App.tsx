// src/App.tsx
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import Register from './components/Register';
import Login from './components/Login';
import Setup from './components/Setup';
import Dashboard from './components/Dashboard';
import './App.css';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/setup" element={<Setup />} /> {/* Đã sửa lỗi ở đây */}
        <Route path='/dashboard' element={<Dashboard />} />
      </Routes>
      <ToastContainer />
    </Router>
  );
}

export default App;