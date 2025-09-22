import { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import './Dashboard.css';
import { Line, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { FiLogOut } from 'react-icons/fi';
import { BsRobot } from 'react-icons/bs';
import { FaUserEdit } from 'react-icons/fa';
import { MdHealthAndSafety } from 'react-icons/md';
import { GiTreeBranch } from 'react-icons/gi';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, Title, Tooltip, Legend);

function Dashboard() {
  const [selectedDay, setSelectedDay] = useState<number | null>(null);
  const [visualData, setVisualData] = useState<any[]>([]);
  const [suggestion, setSuggestion] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>("");
  const [showSuggestion, setShowSuggestion] = useState(false);
  const [showDetail, setShowDetail] = useState(false);
  const [chatInput, setChatInput] = useState('');
  const [chatHistory, setChatHistory] = useState<{role: 'user'|'bot', message: string}[]>([
    { role: 'bot', message: 'Chào bạn, sức khỏe của bạn là ưu tiên hàng đầu. Bạn có đang băn khoăn về tác động của thời tiết, khí hậu, tia UV đến sức khỏe của mình không? Hãy để tôi đồng hành cùng bạn lên kế hoạch để bảo vệ sức khỏe tốt hơn.'}
  ]);
  const [chatLoading, setChatLoading] = useState(false);
  const [currentCityName, setCurrentCityName] = useState<string>("");
  const chatBodyRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const username = sessionStorage.getItem('username');
    const cityId = username ? localStorage.getItem(`city_id_${username}`) : null;
    if (!cityId) {
      setError('Không tìm thấy city_id trong local/session storage');
      setLoading(false);
      return;
    }
    const fetchData = async () => {
      try {
        setLoading(true);
        console.log('Dashboard fetchData BASE_URL:', import.meta.env.VITE_API_BASE_URL, 'cityId:', cityId);
        const resVisual = await fetch(`${import.meta.env.VITE_API_BASE_URL}/get_data_to_visualize/${cityId}`, {
          headers: {
            'ngrok-skip-browser-warning': 'true',
          },
        });
        console.log('resVisual:', resVisual);
        let dataVisual = null;
        const contentType = resVisual.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
          try {
            dataVisual = await resVisual.json();
            console.log('dataVisual:', dataVisual);
          } catch (jsonErr) {
            console.error('Lỗi parse JSON resVisual:', jsonErr);
          }
        } else {
          const text = await resVisual.text();
          console.error('Response text resVisual (not JSON):', text);
        }
        if (dataVisual && dataVisual.status === 'success') {
          setVisualData(dataVisual.data);
        } else {
          setError('Không lấy được dữ liệu visualize');
        }
        // Gọi luôn API lấy suggestion
        const accessToken = sessionStorage.getItem('access_token');
        const resSuggest = await fetch(`${import.meta.env.VITE_API_BASE_URL}/get_passive_suggestion/${cityId}`, {
          headers: {
            'Authorization': accessToken ? `Bearer ${accessToken}` : '',
            'ngrok-skip-browser-warning': 'true',
          },
        });
        console.log('resSuggest:', resSuggest);
        let dataSuggest = null;
        try {
          dataSuggest = await resSuggest.json();
          console.log('dataSuggest:', dataSuggest);
        } catch (jsonErr) {
          console.error('Lỗi parse JSON resSuggest:', jsonErr);
          const text = await resSuggest.text();
          console.error('Response text resSuggest:', text);
        }
        if (dataSuggest && dataSuggest.status === 'success') {
          setSuggestion(dataSuggest.suggestion);
        } else {
          setSuggestion("");
        }
      } catch (err) {
        console.error('API error:', err);
        setError('Lỗi khi gọi API');
      } finally {
        setLoading(false);
      }
    };
    fetchData();

    // Lấy tên tỉnh hiện tại từ localStorage
    const cityName = localStorage.getItem(`city_name_${username}`);
    if (cityName) setCurrentCityName(cityName);
  }, []);

  // Khi click chỉ hiện popup, không fetch lại
  const handleGetSuggestion = () => {
    setShowSuggestion(true);
  };

  // Biểu đồ chi tiết cho ngày đã chọn
  const renderDayDetail = () => {
    if (selectedDay === null || !visualData[selectedDay]) return null;
    const periods = visualData[selectedDay].periods;
    const labels = periods.map((p: any) => p.period);
    // Line chart data
    const feelsLikeData = periods.map((p: any) => Number(p.feels_like));
    const humidityData = periods.map((p: any) => Number(p.humidity));
    const popData = periods.map((p: any) => Math.round(p.pop * 100));
    // Bar chart data
    const pm10Data = periods.map((p: any) => Number(p.pm10));
    const pm25Data = periods.map((p: any) => Number(p.pm2_5));
    const nh3Data = periods.map((p: any) => Number(p.nh3));
    const uviData = periods.map((p: any) => Number(p.uvi));
    // AQI data
    const aqiData = periods.map((p: any) => Number(p.aqi));
    return (
      <div style={{background: '#fff', borderRadius: 16, padding: 24, minWidth: 340, maxWidth: 600, boxShadow: '0 2px 16px #0002', color: '#4A7C59', textAlign: 'center'}}>
        <h3 style={{marginBottom: 16}}>Biểu đồ chi tiết ngày</h3>
        <div style={{marginBottom: 32}}>
          <Line
            data={{
              labels,
              datasets: [
                {
                  label: 'Cảm giác (°C)',
                  data: feelsLikeData,
                  borderColor: '#4A90E2',
                  backgroundColor: 'rgba(74,144,226,0.2)',
                  tension: 0.3,
                },
                {
                  label: 'Độ ẩm (%)',
                  data: humidityData,
                  borderColor: '#50E3C2',
                  backgroundColor: 'rgba(80,227,194,0.2)',
                  tension: 0.3,
                },
                {
                  label: 'Tỷ lệ mưa (%)',
                  data: popData,
                  borderColor: '#F5A623',
                  backgroundColor: 'rgba(245,166,35,0.2)',
                  tension: 0.3,
                },
              ],
            }}
            options={{responsive: true, plugins: {legend: {position: 'top'}}}}
          />
        </div>
        <div style={{marginBottom: 32}}>
          <Bar
            data={{
              labels,
              datasets: [
                {
                  label: 'PM10 (μg/m3)',
                  data: pm10Data,
                  backgroundColor: '#7B9EFA',
                },
                {
                  label: 'PM2.5 (μg/m3)',
                  data: pm25Data,
                  backgroundColor: '#F77E7E',
                },
                {
                  label: 'NH3 (μg/m3)',
                  data: nh3Data,
                  backgroundColor: '#F7D77E',
                },
                {
                  label: 'UVI (μg/m3)',
                  data: uviData,
                  backgroundColor: '#7EF7B2',
                },
              ],
            }}
            options={{responsive: true, plugins: {legend: {position: 'top'}}}}
          />
        </div>
        <div style={{marginBottom: 16}}>
          <h4>AQI các buổi trong ngày</h4>
          <div style={{display: 'flex', justifyContent: 'center', gap: 12}}>
            {aqiData.map((aqi: number, idx: number) => (
              <div key={idx} style={{padding: '8px 12px', borderRadius: 8, background: aqi === 1 ? '#7ef7b2' : aqi === 2 ? '#f7f77e' : aqi === 3 ? '#f7d77e' : aqi === 4 ? '#f7a77e' : '#f77e7e', color: '#222', fontWeight: 'bold', minWidth: 48}}>
                {labels[idx]}<br/>AQI: {aqi}
              </div>
            ))}
          </div>
        </div>
        <button className="primary-btn" style={{marginTop: 24}} onClick={() => setShowDetail(false)}>Đóng</button>
      </div>
    );
  };

  // Hàm render suggestion với định dạng đẹp
  const renderSuggestion = (text: string) => {
    // Tách theo **...**
    const parts = text.split(/(\*\*[^*]+\*\*)/g);
    return parts.map((part, idx) => {
      if (/^\*\*[^*]+\*\*$/.test(part)) {
        // Bỏ ** và in đậm, xuống dòng trước
        return <div key={idx} style={{marginTop: 8, fontWeight: 'bold'}}>{part.replace(/\*\*/g, '')}</div>;
      }
      // Nếu là đoạn văn bản thường, giữ nguyên
      return <span key={idx}>{part}</span>;
    });
  };

  // Tự động cuộn xuống cuối khi có tin nhắn mới
  useEffect(() => {
    if (chatBodyRef.current) {
      chatBodyRef.current.scrollTop = chatBodyRef.current.scrollHeight;
    }
  }, [chatHistory, showSuggestion, showDetail]);

  // Gửi tin nhắn chatbot
  const handleSendChat = async () => {
    if (!chatInput.trim() || chatLoading) return;
    setChatLoading(true);
    const username = sessionStorage.getItem('username');
    const cityId = username ? localStorage.getItem(`city_id_${username}`) : null;
    const accessToken = sessionStorage.getItem('access_token');
    if (!cityId || !accessToken) {
      setChatLoading(false);
      return;
    }
    setChatHistory(prev => [...prev, { role: 'user', message: chatInput }]);
    setChatInput('');
    try {
      console.log('Gửi chatbot:', { cityId, chatInput });
      const res = await fetch(`${import.meta.env.VITE_API_BASE_URL}/submit_chatbot_query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`,
          'ngrok-skip-browser-warning': 'true',
        },
        body: JSON.stringify({
          city_id: cityId,
          user_input: chatInput
        })
      });
      console.log('Response submit_chatbot_query:', res);
      let data = null;
      try {
        data = await res.json();
        console.log('Data submit_chatbot_query:', data);
      } catch (jsonErr) {
        console.error('Lỗi parse JSON submit_chatbot_query:', jsonErr);
        const text = await res.text();
        console.error('Response text submit_chatbot_query:', text);
      }
      if (res.ok && data && data.request_id) {
        let result = null;
        let tries = 0;
        while (!result && tries < 30) {
          await new Promise(r => setTimeout(r, 1000));
          const res2 = await fetch(`${import.meta.env.VITE_API_BASE_URL}/get_chatbot_result/${data.request_id}`, {
            headers: {
              'Authorization': `Bearer ${accessToken}`,
              'ngrok-skip-browser-warning': 'true',
            }
          });
          console.log(`Polling lần ${tries + 1}:`, res2);
          let data2 = null;
          try {
            data2 = await res2.json();
            console.log(`Data polling lần ${tries + 1}:`, data2);
          } catch (jsonErr2) {
            console.error(`Lỗi parse JSON polling lần ${tries + 1}:`, jsonErr2);
            const text2 = await res2.text();
            console.error(`Response text polling lần ${tries + 1}:`, text2);
          }
          if (res2.status === 200 && data2 && data2.status === 'completed' && data2.data) {
            result = data2.data;
            break;
          }
          tries++;
        }
        if (result) {
          setChatHistory(prev => [...prev, { role: 'bot', message: result }]);
        } else {
          setChatHistory(prev => [...prev, { role: 'bot', message: 'Chatbot không phản hồi. Vui lòng thử lại sau.' }]);
        }
      } else {
        setChatHistory(prev => [...prev, { role: 'bot', message: 'Không gửi được yêu cầu đến chatbot.' }]);
      }
    } catch (e) {
      console.error('Lỗi khi gửi hoặc nhận phản hồi từ chatbot:', e);
      setChatHistory(prev => [...prev, { role: 'bot', message: 'Có lỗi khi gửi hoặc nhận phản hồi từ chatbot.' }]);
    } finally {
      setChatLoading(false);
    }
  };

  // Hàm format nội dung trả về từ chatbot: in đậm **...**, liệt kê *..., giữ đoạn văn liền mạch
  const formatChatbotMessage = (text: string) => {
    // Tách thành từng dòng theo dấu * ở đầu dòng hoặc **...**
    // 1. Tách theo dấu xuống dòng hoặc dấu * đầu dòng
    const lines = text.split(/\n|(?=\* )|(?=\*\*)/g).map(l => l.trim()).filter(l => l);
    return lines.map((line, idx) => {
      // In đậm **...**
      if (/^\*\*[^*]+\*\*/.test(line)) {
        return <div key={idx} style={{fontWeight: 'bold', margin: '8px 0 4px 0'}}>{line.replace(/\*\*/g, '')}</div>;
      }
      // Liệt kê * ... (bỏ luôn dấu *)
      if (/^\* /.test(line)) {
        return <div key={idx} style={{marginLeft: 18, marginBottom: 2}}>• {line.replace(/^\* /, '').replace(/^\*/, '').trim()}</div>;
      }
      // Nếu là dòng thường
      return <div key={idx} style={{margin: '4px 0'}}>{line.replace(/^\*/, '').trim()}</div>;
    });
  };

  return (
    <div className="dashboard-layout">
      <div className="dashboard-main">
        <div className="dashboard-toolbar" style={{display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 18, padding: '12px 0'}}>
          <div>
            <span style={{ color: "#000000f3", fontWeight: 600, fontSize: "12px" }}>
              <strong> Tỉnh hiện tại:</strong>
            </span>
            <span style={{ color: "#c25489ff", fontWeight: 600, fontSize: "18px" }}>
              {currentCityName}
            </span>
          </div>
          <button className="toolbar-btn" style={{display: 'flex', alignItems: 'center', gap: 8, fontWeight: 500, fontSize: '1rem'}} onClick={() => navigate('/setup')}>
            <FaUserEdit size={20} color="#4A7C59" />
            Cập nhật thông tin
          </button>
          <button className="toolbar-btn" style={{display: 'flex', alignItems: 'center', gap: 8, fontWeight: 500, fontSize: '1rem', marginLeft: 0}} onClick={handleGetSuggestion}>
            <MdHealthAndSafety size={22} color="#d33737ff" />
            Nhận lời khuyên hôm nay
            <GiTreeBranch size={20} color="#72ec9bff" style={{marginLeft: 4}} />
            {suggestion && (
              <span style={{position: 'absolute', top: 6, right: 6, width: 12, height: 12, background: 'red', borderRadius: '50%', display: 'inline-block', border: '2px solid #fff'}}></span>
            )}
          </button>
        </div>
        <div className="dashboard-3col">
          {/* Cột trái: Chọn ngày */}
          <div className="dashboard-days">
            <div className="days-list">
              {visualData.map((day, idx) => {
                const weekday = (new Date(day.year, day.month - 1, day.day).getDay() + 1) % 8 || 1; // Chủ nhật là 1
                const weekdayText =
                  weekday === 1 ? 'Chủ nhật' : `Thứ ${weekday}`;
                return (
                  <button
                    key={idx}
                    className={`day-card ${selectedDay === idx ? 'active' : ''}`}
                    onClick={() => setSelectedDay(idx)}
                  >
                    {`${weekdayText}, ${day.day}/${day.month}`}
                  </button>
                );
              })}
            </div>
            <div style={{margin: '18px 0 8px 0', color: '#865858ff', fontSize: '0.98rem', textAlign: 'center', lineHeight: 1.5, fontWeight: 500}}>
              Dữ liệu thời tiết, khí hậu sẽ được cập nhật hằng ngày.<br/>
              Nếu bạn muốn thay đổi thông tin nơi ở, tình trạng sức khỏe,<br/>
              hãy sử dụng nút cập nhật trên thanh công cụ phía trên.
            </div>
            <button
              className="logout-btn"
              style={{
                display: 'flex', alignItems: 'center', gap: 8, margin: '18px auto 0 auto', padding: '8px 18px', border: 'none', background: '#f77e7e', color: '#fff', borderRadius: 8, fontWeight: 500, cursor: 'pointer', fontSize: '1rem', boxShadow: '0 2px 8px #0001'
              }}
              onClick={() => {
                sessionStorage.clear();
                navigate('/login');
              }}
            >
              <FiLogOut size={22} />
              Đăng xuất
            </button>
          </div>

          {/* Cột giữa: Thông tin thời tiết */}
          <div className="dashboard-weather" style={{
            maxHeight: '85vh',
            overflowY: 'auto',
            paddingRight: 8
          }}>
            {loading ? (
              <div className="weather-placeholder">Đang tải dữ liệu...</div>
            ) : error ? (
              <div className="weather-placeholder">{error}</div>
            ) : selectedDay !== null && visualData[selectedDay] ? (
              <div style={{display: 'flex', flexWrap: 'wrap', gap: '20px', justifyContent: 'center', alignItems: 'flex-start', width: '100%', background: 'none', boxShadow: 'none', border: 'none'}}>
                {visualData[selectedDay].periods.map((p: any, i: number) => (
                  <div
                    key={i}
                    style={{
                      background: '#91bae2ff',
                      borderRadius: 14,
                      border: '2px solid #222',
                      boxShadow: '0 2px 8px #0001',
                      padding: '8px 12px',
                      width: '48%',
                      minWidth: 140,
                      maxWidth: 200,
                      textAlign: 'center',
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      justifyContent: 'center',
                      boxSizing: 'border-box',
                    }}
                  >
                    <div style={{fontWeight: 'bold', marginBottom: 3, fontSize: '1.05rem'}}>{p.period}</div>
                    <img src={`https://openweathermap.org/img/wn/${p.weather_icon}.png`} alt={p.weather_description} style={{width: 32, height: 32, marginBottom: 4}} />
                    <div style={{margin: '4px 0', fontWeight: 500, fontSize: '0.98rem'}}>{p.weather_description}</div>
                    <div style={{fontSize: '1.05rem', fontWeight: 'bold', marginBottom: 2}}>{Number(p.temp).toFixed(2)}°C</div>
                    <div style={{fontSize: '0.95rem', marginBottom: 2}}>Cảm giác: {Number(p.feels_like).toFixed(2)}°C</div>
                    <div style={{fontSize: '0.92rem', marginBottom: 2}}>Độ ẩm: {p.humidity}%</div>
                    <div style={{fontSize: '0.92rem', marginBottom: 2}}>Gió: {Number(p.wind_speed).toFixed(2)} m/s</div>
                    <div style={{fontSize: '0.92rem', marginBottom: 2}}>Tỷ lệ mưa: {Math.round(p.pop * 100)}%</div>
                    <div style={{fontSize: '0.92rem'}}>AQI: {p.aqi} | UVI: {Number(p.uvi).toFixed(2)}</div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="weather-placeholder">Chọn một ngày để xem chi tiết thời tiết</div>
            )}
            {selectedDay !== null && visualData[selectedDay] && (
              <div style={{width: '10%', textAlign: 'right', marginTop: 24}}>
                <button className="primary-btn" style={{fontSize: '0.95rem', padding: '6px 18px'}} onClick={() => setShowDetail(true)}>
                  Xem chi tiết
                </button>
              </div>
            )}
            {showDetail && (
              <div style={{position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: '#0005', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 999}}>
                <div style={{background: '#fff', borderRadius: 16, padding: 24, minWidth: 340, maxWidth: 600, maxHeight: '80vh', boxShadow: '0 2px 16px #0002', color: '#4A7C59', textAlign: 'center', overflowY: 'auto'}}>
                  {renderDayDetail()}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Popup lời khuyên */}
      {showSuggestion && suggestion && (
        <div className="suggestion-popup" style={{position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: '#0005', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 999}}>
          <div style={{background: '#fff', borderRadius: 16, padding: 32, minWidth: 320, maxWidth: 500, maxHeight: '80vh', boxShadow: '0 2px 16px #0002', color: '#4A7C59', textAlign: 'left', overflowY: 'auto'}}>
            <strong>Lời khuyên hôm nay:</strong>
            <div style={{marginTop: 16, whiteSpace: 'pre-line', lineHeight: 1.7}}>{renderSuggestion(suggestion)}</div>
            <button className="primary-btn" style={{marginTop: 24}} onClick={() => setShowSuggestion(false)}>Đóng</button>
          </div>
        </div>
      )}

      {/* Cột phải: Chatbot */}
      <div className="dashboard-chatbot">
        <div className="chatbot-body" ref={chatBodyRef}>
          {chatHistory.map((msg, idx) => (
            msg.role === 'bot' ? (
              <div key={idx} className="chat-message bot" style={{display: 'flex', alignItems: 'flex-start', gap: 8}}>
                <BsRobot size={32} color="#4A90E2" style={{marginRight: 6, marginTop: 2}} />
                <div style={{flex: 1}}>{formatChatbotMessage(msg.message)}</div>
              </div>
            ) : (
              <div key={idx} className="chat-message user">{msg.message}</div>
            )
          ))}
          {chatLoading && (
            <div className="chat-message bot" style={{display: 'flex', alignItems: 'flex-start', gap: 8}}>
              <BsRobot size={32} color="#4A90E2" style={{marginRight: 6, marginTop: 2}} />
              <div style={{flex: 1}}>Đang trả lời...</div>
            </div>
          )}
        </div>
        <div className="chatbot-input">
          <input
            type="text"
            placeholder="Nhập tin nhắn..."
            value={chatInput}
            onChange={e => setChatInput(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && chatInput.trim() && !chatLoading) handleSendChat(); }}
            disabled={chatLoading}
          />
          <button className="primary-btn" onClick={handleSendChat} disabled={!chatInput.trim() || chatLoading}>Gửi</button>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;