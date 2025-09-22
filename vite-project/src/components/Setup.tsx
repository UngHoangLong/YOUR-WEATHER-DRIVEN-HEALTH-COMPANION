// src/components/Setup.tsx
import { useState } from 'react';
import type { FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import './Form.css';
import './Setup.css';

// Import images for diseases. 
// Assuming these are located in the src/assets/image directory.
import respiratoryImage from '/assets/image/respiratory.jpg';
import allergyImage from '/assets/image/allergy.jpg';
import heatImage from '/assets/image/heat.jpg';
import cardiovascularImage from '/assets/image/cardiovascular.jpg';


// Dữ liệu danh sách tỉnh thành
const cities = [
    { id: '1594446', name: 'An Giang' },
    { id: '1905419', name: 'Bắc Giang' },
    { id: '1905669', name: 'Bắc Kạn' },
    { id: '1905412', name: 'Bắc Ninh' },
    { id: '1905675', name: 'Bạc Liêu' },
    { id: '1584534', name: 'Bà Rịa - Vũng Tàu' },
    { id: '1587974', name: 'Bến Tre' },
    { id: '1587871', name: 'Bình Định' },
    { id: '1905475', name: 'Bình Dương' },
    { id: '1905480', name: 'Bình Phước' },
    { id: '1581882', name: 'Bình Thuận' },
    { id: '1905678', name: 'Cà Mau' },
    { id: '1581188', name: 'Cần Thơ' },
    { id: '1586182', name: 'Cao Bằng' },
    { id: '1905468', name: 'Đà Nẵng' },
    { id: '1584169', name: 'Đắk Lắk' },
    { id: '1905099', name: 'Điện Biên' },
    { id: '1582720', name: 'Đồng Nai' },
    { id: '1582562', name: 'Đồng Tháp' },
    { id: '1581088', name: 'Gia Lai' },
    { id: '1581030', name: 'Hà Giang' },
    { id: '1905637', name: 'Hà Nam' },
    { id: '1581129', name: 'Hà Nội' },
    { id: '1580700', name: 'Hà Tĩnh' },
    { id: '1905686', name: 'Hải Dương' },
    { id: '1581297', name: 'Hải Phòng' },
    { id: '1572594', name: 'Hòa Bình' },
    { id: '1905699', name: 'Hưng Yên' },
    { id: '1579634', name: 'Khánh Hòa' },
    { id: '1579008', name: 'Kiên Giang' },
    { id: '1565088', name: 'Kon Tum' },
    { id: '1577882', name: 'Lâm Đồng' },
    { id: '1576632', name: 'Lạng Sơn' },
    { id: '1562412', name: 'Lào Cai' },
    { id: '1575788', name: 'Long An' },
    { id: '1905626', name: 'Nam Định' },
    { id: '1559969', name: 'Nghệ An' },
    { id: '1559970', name: 'Ninh Bình' },
    { id: '1559971', name: 'Ninh Thuận' },
    { id: '1569805', name: 'Phú Yên' },
    { id: '1905577', name: 'Phú Thọ' },
    { id: '1568839', name: 'Quảng Bình' },
    { id: '1905516', name: 'Quảng Nam' },
    { id: '1568769', name: 'Quảng Ngãi' },
    { id: '1568758', name: 'Quảng Ninh' },
    { id: '1568733', name: 'Quảng Trị' },
    { id: '1567643', name: 'Sơn La' },
    { id: '1559972', name: 'Sóc Trăng' },
    { id: '1566338', name: 'Thái Bình' },
    { id: '1905497', name: 'Thái Nguyên' },
    { id: '1566165', name: 'Thanh Hóa' },
    { id: '1565033', name: 'Thừa Thiên-Huế' },
    { id: '1564676', name: 'Tiền Giang' },
    { id: '1580578', name: 'TP. Hồ Chí Minh' },
    { id: '1559975', name: 'Trà Vinh' },
    { id: '1559976', name: 'Tuyên Quang' },
    { id: '1559977', name: 'Vĩnh Long' },
    { id: '1905856', name: 'Vĩnh Phúc' },
    { id: '1559978', name: 'Yên Bái' },
    { id: '1566557', name: 'Tây Ninh' },
];

// Cập nhật mảng diseasesWithImages với các ví dụ cụ thể
const diseasesWithImages = [
    { id: 1, name: <strong>Bệnh về hô hấp</strong>, image: respiratoryImage, description: 'Ví dụ: Hen suyễn, viêm phổi tắc nghẽn mãn tính (COPD), viêm phế quản...' },
    { id: 2, name: <strong>Dị ứng</strong>, image: allergyImage, description: 'Ví dụ: Viêm mũi dị ứng, dị ứng phấn hoa, dị ứng thời tiết...' },
    { id: 3, name: <strong>Các bệnh liên quan đến nhiệt độ</strong>, image: heatImage, description: 'Ví dụ: Đột quỵ nhiệt, sốc nhiệt, say nắng...' },
    { id: 4, name: <strong>Tim mạch</strong>, image: cardiovascularImage, description: 'Ví dụ: Huyết áp cao, nhồi máu cơ tim, đột quỵ...' },
];

function Setup() {
    const [selectedCity, setSelectedCity] = useState(localStorage.getItem(`city_id_${sessionStorage.getItem('username')}`) || '');
    const [selectedDisease, setSelectedDisease] = useState(localStorage.getItem(`disease_id_${sessionStorage.getItem('username')}`) || '');
    const [diseaseDescription, setDiseaseDescription] = useState(localStorage.getItem(`disease_description_${sessionStorage.getItem('username')}`) || '');
    const navigate = useNavigate();

    const handleNoDiseaseClick = () => {
        setSelectedDisease('5');
    };

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();

        // Lấy token và username mới nhất từ sessionStorage
        const token = sessionStorage.getItem('access_token');
        const username = sessionStorage.getItem('username');

        if (!selectedCity || !selectedDisease) {
            toast.error('Vui lòng chọn đầy đủ tỉnh thành và nhóm bệnh.');
            return;
        }

        if (!token || !username) {
            toast.error('Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.');
            navigate('/login');
            return;
        }

        try {
            const requests = [];

            // Luôn thêm yêu cầu cập nhật thành phố
            requests.push(
                fetch(`${import.meta.env.VITE_API_BASE_URL}/update_city_info_for_user`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`,
                        'ngrok-skip-browser-warning': 'true',
                    },
                    body: JSON.stringify({
                        city_id: parseInt(selectedCity, 10)
                    }),
                })
            );

            // Chỉ thêm yêu cầu cập nhật bệnh nếu người dùng chọn bệnh cụ thể
            if (selectedDisease && selectedDisease !== '5') {
                requests.push(
                    fetch(`${import.meta.env.VITE_API_BASE_URL}/update_disease`, {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${token}`,
                            'ngrok-skip-browser-warning': 'true',
                        },
                        body: JSON.stringify({
                            disease_id: parseInt(selectedDisease, 10),
                            describe_disease: diseaseDescription,
                        }),
                    })
                );
            }

            const responses = await Promise.all(requests);

            // Xử lý các phản hồi một cách linh hoạt
            for (const response of responses) {
                if (!response.ok) {
                    const errorData = await response.json();
                    toast.error(errorData.detail || 'Có lỗi xảy ra trong quá trình cập nhật.');
                    return;
                }
            }
            
            // Nếu mọi thứ đều OK, cập nhật localStorage và chuyển hướng
            const cityInfo = cities.find(city => city.id === selectedCity);
            if (cityInfo) {
                localStorage.setItem(`city_id_${username}`, selectedCity);
                localStorage.setItem(`city_name_${username}`, cityInfo.name);
            }

            // Lưu thông tin bệnh nền vào localStorage
            localStorage.setItem(`disease_id_${username}`, selectedDisease);
            localStorage.setItem(`disease_description_${username}`, diseaseDescription);

            // Lưu cờ đánh dấu người dùng đã setup thành công
            localStorage.setItem(`is_setup_${username}`, 'true');

            toast.success('Cập nhật thông tin thành công!', {
                onClose: () => navigate('/dashboard')
            });

        } catch (error) {
            toast.error('Không thể kết nối đến máy chủ. Vui lòng thử lại sau.');
        }
    };

    return (
        <div className="setup-page-container">
            <div className="setup-card">
                <h1 className="logo-text">Thiết lập hồ sơ cá nhân </h1>
                <p className="slogan-text">Hãy cung cấp một vài thông tin về nơi bạn đang sống cũng như sức khỏe để chúng tôi hỗ trợ bạn tốt hơn.</p>
                <form className="form" onSubmit={handleSubmit}>
                    <div className="input-group">
                        <label htmlFor="city-select" className="form-label">
                            <strong>Chọn tỉnh thành:</strong>
                        </label>
                        <p className="note-text">
                            Để chúng tôi hỗ trợ bạn tốt nhất, vui lòng chọn tỉnh thành. Việc này giúp chúng tôi cập nhật dữ liệu tại địa phương và đưa ra những lời khuyên phù hợp nhất với điều kiện nơi bạn sống.
                        </p>
                        <select
                            id="city-select"
                            value={selectedCity}
                            onChange={(e) => setSelectedCity(e.target.value)}
                            className="input-field dark-input"
                        >
                            <option value="">-- Chọn một tỉnh thành --</option>
                            {cities.map((city) => (
                                <option key={city.id} value={city.id}>
                                    {city.name}
                                </option>
                            ))}
                        </select>
                    </div>
                    <div className="input-group">
                        <label className="form-label"><strong>Nhóm bệnh mà bạn đang mắc phải (nếu có)</strong>:</label>
                        <p className="note-text">
                            Khi bạn chia sẻ thông tin về bệnh nền, chúng tôi có thể mang đến những lời khuyên sức khỏe hằng ngày được cá nhân hóa, dựa trên dữ liệu thời tiết và khí hậu, giúp bạn chủ động chăm sóc bản thân tốt hơn.
                        </p>
                        <div className="disease-options">
                            {diseasesWithImages.map((disease) => (
                                <div
                                    key={disease.id}
                                    className={`disease-item ${selectedDisease === disease.id.toString() ? 'selected' : ''}`}
                                    onClick={() => setSelectedDisease(disease.id.toString())}
                                >
                                    <img src={disease.image} alt={typeof disease.name === 'string' ? disease.name : undefined} className="disease-image" />
                                    <span className="disease-name">{disease.name}</span>
                                    {/* Thêm mô tả cụ thể về bệnh */}
                                    <span className="disease-description">{disease.description}</span>
                                </div>
                            ))}
                        </div>
                        <button
                            type="button"
                            className={`no-disease-button ${selectedDisease === '5' ? 'selected' : ''}`}
                            onClick={handleNoDiseaseClick}
                        >
                            Không có bệnh nền
                        </button>
                    </div>
                    <div className="input-group">
                        <label htmlFor="describe" className="form-label"><strong>Mô tả thêm về tình trạng sức khỏe:</strong></label>
                        <textarea
                            id="describe"
                            placeholder="Mỗi sáng mình thường bị hắt hơi liên tục, mũi thì ngứa và chảy nước mũi trong suốt; mắt hay đỏ, ngứa và chảy nước mắt khiến mình rất khó chịu..."
                            value={diseaseDescription}
                            onChange={(e) => setDiseaseDescription(e.target.value)}
                            className="input-field dark-input"
                            rows={4}
                        />
                    </div>
                    <p className="note-text">
                        <strong>Những thiết lập này bạn có thể cập nhật lại bất cứ lúc nào trong phần hồ sơ cá nhân.</strong>
                    </p>
                    <button type="submit" className="form-button primary-button">Lưu Cài Đặt</button>
                </form>
            </div>
        </div>
    );
}

export default Setup;
