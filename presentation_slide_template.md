# 🎬 MOVIE MATE v2 - SLIDE TEMPLATE

## Phối màu: Đỏ (#DC2626) + Xám (#6B7280)

---

## 📋 **SLIDE 1: TITLE SLIDE**

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  [Logo Movie Mate]                                      │
│                                                         │
│                                                         │
│     🎬 MOVIE MATE v2                                    │
│                                                         │
│  Hệ Thống Khuyến Nghị Phim Thông Minh                  │
│                                                         │
│                                                         │
│  [Tên nhóm/người thực hiện]                            │
│  [Ngày thuyết trình]                                   │
│                                                         │
└─────────────────────────────────────────────────────────┘

Background: Gradient từ đỏ (#DC2626) sang xám đậm (#1F2937)
Text: Trắng (#FFFFFF)
Accent: Icon phim màu đỏ nhạt (#FEE2E2)
```

---

## 📋 **SLIDE 2: TỔNG QUAN DỰ ÁN**

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  📊 TỔNG QUAN DỰ ÁN                                     │
│                                                         │
│  ┌─────────────────┐  ┌─────────────────┐              │
│  │ 🎯 Mục Tiêu     │  │ 👥 Đối Tượng    │              │
│  │                 │  │                 │              │
│  │ Xây dựng hệ     │  │ Người dùng yêu  │              │
│  │ thống khuyến    │  │ thích phim ảnh  │              │
│  │ nghị thông minh │  │                 │              │
│  └─────────────────┘  └─────────────────┘              │
│                                                         │
│  ┌─────────────────┐  ┌─────────────────┐              │
│  │ 📈 Quy Mô       │  │ 🛠️ Công Nghệ    │              │
│  │                 │  │                 │              │
│  │ Hệ thống        │  │ Django + React  │              │
│  │ full-stack với   │  │ + PostgreSQL    │              │
│  │ AI/ML           │  │ + Elasticsearch │              │
│  └─────────────────┘  └─────────────────┘              │
│                                                         │
└─────────────────────────────────────────────────────────┘

Background: Trắng (#FFFFFF)
Headers: Đỏ (#DC2626)
Boxes: Border đỏ nhạt (#FEE2E2), Background xám nhạt (#F3F4F6)
Text: Xám đậm (#374151)
Icons: Đỏ (#DC2626)
```

---

## 📋 **SLIDE 3: KIẾN TRÚC HỆ THỐNG**

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  🏗️ KIẾN TRÚC HỆ THỐNG                                 │
│                                                         │
│  ┌─────────────────┐    ┌─────────────────┐            │
│  │   React         │    │  Django         │            │
│  │   Frontend      │◄──►│  Backend        │            │
│  │                 │    │                 │            │
│  │   • User UI     │    │   • REST API    │            │
│  │   • Admin Panel │    │   • ML Engine   │            │
│  └─────────────────┘    └─────────────────┘            │
│                                │                        │
│                                ▼                        │
│                       ┌─────────────────┐              │
│                       │  PostgreSQL     │              │
│                       │                 │              │
│                       │   • Movie Data  │              │
│                       │   • User Data   │              │
│                       └─────────────────┘              │
│                                                         │
│  ┌─────────────────┐    ┌─────────────────┐            │
│  │  Elasticsearch  │    │     Redis       │            │
│  │   • Search      │    │   • Cache       │            │
│  │   • Analytics   │    │   • Sessions    │            │
│  └─────────────────┘    └─────────────────┘            │
│                                                         │
└─────────────────────────────────────────────────────────┘

Background: Xám nhạt (#F9FAFB)
Headers: Đỏ gradient (#DC2626 → #B91C1C)
Boxes: Border đỏ (#DC2626), Background trắng (#FFFFFF)
Arrows: Đỏ (#DC2626)
Text: Xám đậm (#374151)
```

---

## 📋 **SLIDE 4: CÁC THUẬT TOÁN KHUYẾN NGHỊ**

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  🤖 CÔNG NGHỆ AI/ML                                     │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 1️⃣ COLLABORATIVE FILTERING                      │   │
│  │                                                │   │
│  │ • User-based: Tìm người dùng tương tự          │   │
│  │ • Item-based: Tìm phim tương tự                │   │
│  │ • Matrix Factorization: Phân tích ma trận      │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 2️⃣ CONTENT-BASED FILTERING                      │   │
│  │                                                │   │
│  │ • Phân tích thể loại, diễn viên, đạo diễn      │   │
│  │ • TF-IDF cho mô tả phim                        │   │
│  │ • Cosine similarity                            │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 3️⃣ HYBRID APPROACH                              │   │
│  │                                                │   │
│  │ • Kết hợp nhiều thuật toán                     │   │
│  │ • Weighted scoring                             │   │
│  │ • Context-aware recommendations                │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘

Background: Trắng (#FFFFFF)
Headers: Đỏ (#DC2626)
Numbered boxes: Border đỏ nhạt (#FEE2E2), Background xám nhạt (#F3F4F6)
Bullet points: Xám đậm (#374151)
Icons: Đỏ (#DC2626)
```

---

## 📋 **SLIDE 5: TÍNH NĂNG CHÍNH**

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  ⭐ CÁC MODULE CHỨC NĂNG                               │
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ 🎬 Quản Lý  │  │ 👤 Quản Lý  │  │ ⭐ Hệ Thống │     │
│  │    Phim     │  │  Người Dùng │  │  Đánh Giá   │     │
│  │             │  │             │  │             │     │
│  │ • Crawl     │  │ • Auth      │  │ • Rating    │     │
│  │ • Metadata  │  │ • Profile   │  │ • Review    │     │
│  │ • Quality   │  │ • Plans     │  │ • Moderation│     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ 🤖 Khuyến   │  │ 📊 Analytics│  │ 🛡️ Content  │     │
│  │   Nghị      │  │             │  │  Moderation │     │
│  │             │  │             │  │             │     │
│  │ • Personal  │  │ • Behavior  │  │ • Spoiler   │     │
│  │ • Trending  │  │ • Metrics   │  │ • Review    │     │
│  │ • Genre     │  │ • Reports   │  │ • Approval  │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│                                                         │
└─────────────────────────────────────────────────────────┘

Background: Xám nhạt (#F9FAFB)
Headers: Đỏ (#DC2626)
Feature boxes: Border đỏ (#DC2626), Background trắng (#FFFFFF)
Icons: Đỏ (#DC2626)
Text: Xám đậm (#374151)
```

---

## 📋 **SLIDE 6: DEMO - GIAO DIỆN NGƯỜI DÙNG**

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  🖥️ TRẢI NGHIỆM NGƯỜI DÙNG                             │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ [SCREENSHOT: Homepage]                          │   │
│  │                                                │   │
│  │ • Hero banner với trending movies              │   │
│  │ • Personalized recommendations                 │   │
│  │ • Search bar với Elasticsearch                 │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────┐  ┌─────────────────┐              │
│  │ [Movie Details] │  │ [User Profile]  │              │
│  │                 │  │                 │              │
│  │ • Thông tin     │  │ • Watchlist     │              │
│  │   chi tiết      │  │ • Ratings       │              │
│  │ • Cast & Crew   │  │ • Preferences   │              │
│  │ • Trailers      │  │ • History       │              │
│  └─────────────────┘  └─────────────────┘              │
│                                                         │
└─────────────────────────────────────────────────────────┘

Background: Trắng (#FFFFFF)
Headers: Đỏ (#DC2626)
Screenshots: Border đỏ nhạt (#FEE2E2)
Captions: Xám đậm (#374151)
```

---

## 📋 **SLIDE 7: DEMO - ADMIN DASHBOARD**

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  ⚙️ QUẢN TRỊ HỆ THỐNG                                  │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ [SCREENSHOT: Admin Dashboard]                   │   │
│  │                                                │   │
│  │ 📊 Analytics Dashboard                         │   │
│  │ • User metrics & performance                   │   │
│  │ • Movie trending analysis                      │   │
│  │ • System health monitoring                     │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────┐  ┌─────────────────┐              │
│  │ 🎬 Movie Mgmt   │  │ 👥 User Mgmt    │              │
│  │                 │  │                 │              │
│  │ • CRUD ops      │  │ • User analytics│              │
│  │ • Approval      │  │ • Moderation    │              │
│  │ • Quality check │  │ • Permissions   │              │
│  └─────────────────┘  └─────────────────┘              │
│                                                         │
└─────────────────────────────────────────────────────────┘

Background: Xám nhạt (#F9FAFB)
Headers: Đỏ (#DC2626)
Screenshots: Border đỏ nhạt (#FEE2E2)
Feature boxes: Border đỏ (#DC2626), Background trắng (#FFFFFF)
```

---

## 📋 **SLIDE 8: CÔNG NGHỆ SỬ DỤNG**

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  🛠️ TECH STACK CHI TIẾT                               │
│                                                         │
│  ┌─────────────────┐  ┌─────────────────┐              │
│  │ 🎨 Frontend     │  │ ⚙️ Backend      │              │
│  │                 │  │                 │              │
│  │ • React 18      │  │ • Django 4.0+   │              │
│  │ • Redux Toolkit │  │ • DRF           │              │
│  │ • Tailwind CSS  │  │ • PostgreSQL    │              │
│  │ • Material-UI   │  │ • Elasticsearch │              │
│  │ • React Query   │  │ • Redis         │              │
│  │ • Framer Motion │  │ • Celery        │              │
│  └─────────────────┘  └─────────────────┘              │
│                                                         │
│  ┌─────────────────┐  ┌─────────────────┐              │
│  │ 🔧 DevOps       │  │ 🚀 Performance  │              │
│  │                 │  │                 │              │
│  │ • Docker        │  │ • < 200ms API   │              │
│  │ • CI/CD         │  │ • 99.9% uptime  │              │
│  │ • Monitoring    │  │ • Auto-scaling  │              │
│  │ • Testing       │  │ • Caching       │              │
│  └─────────────────┘  └─────────────────┘              │
│                                                         │
└─────────────────────────────────────────────────────────┘

Background: Trắng (#FFFFFF)
Headers: Đỏ (#DC2626)
Tech boxes: Border đỏ (#DC2626), Background xám nhạt (#F3F4F6)
Icons: Đỏ (#DC2626)
Text: Xám đậm (#374151)
```

---

## 📋 **SLIDE 9: DỮ LIỆU VÀ HIỆU SUẤT**

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  📊 QUY MÔ DỮ LIỆU & HIỆU SUẤT                         │
│                                                         │
│  ┌─────────────────┐  ┌─────────────────┐              │
│  │ 🎬 Movies       │  │ 👥 Users        │              │
│  │                 │  │                 │              │
│  │ 50,000+ phim    │  │ Hàng nghìn      │              │
│  │ với metadata    │  │ người dùng      │              │
│  │ đầy đủ          │  │ đồng thời       │              │
│  └─────────────────┘  └─────────────────┘              │
│                                                         │
│  ┌─────────────────┐  ┌─────────────────┐              │
│  │ ⭐ Ratings      │  │ ⚡ Performance   │              │
│  │                 │  │                 │              │
│  │ Hệ thống đánh   │  │ Response time   │              │
│  │ giá real-time   │  │ < 200ms         │              │
│  │                 │  │ 99.9% uptime    │              │
│  └─────────────────┘  └─────────────────┘              │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 📈 Scalability: Microservices Architecture     │   │
│  │ 🛡️ Security: JWT, HTTPS, Data Encryption      │   │
│  │ 🔄 Real-time: WebSocket, Live Updates         │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘

Background: Xám nhạt (#F9FAFB)
Headers: Đỏ (#DC2626)
Metric boxes: Border đỏ (#DC2626), Background trắng (#FFFFFF)
Numbers: Đỏ (#DC2626)
Text: Xám đậm (#374151)
```

---

## 📋 **SLIDE 10: TÍNH NĂNG NỔI BẬT**

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  🌟 ĐIỂM KHÁC BIỆT                                     │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 🎯 AI-Powered Recommendations                   │   │
│  │                                                │   │
│  │ • Multi-algorithm approach                     │   │
│  │ • Real-time learning                          │   │
│  │ • Context-aware suggestions                   │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 🛡️ Content Moderation                           │   │
│  │                                                │   │
│  │ • Automated spoiler detection                  │   │
│  │ • AI-powered review analysis                   │   │
│  │ • Manual approval workflow                     │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 📊 Advanced Analytics                           │   │
│  │                                                │   │
│  │ • User behavior tracking                       │   │
│  │ • Performance metrics                          │   │
│  │ • Trending analysis                            │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 🌐 Multi-language Support                       │   │
│  │                                                │   │
│  │ • Vietnamese + English                         │   │
│  │ • Localized content                            │   │
│  │ • Cultural adaptation                          │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘

Background: Trắng (#FFFFFF)
Headers: Đỏ (#DC2626)
Feature boxes: Border đỏ nhạt (#FEE2E2), Background xám nhạt (#F3F4F6)
Icons: Đỏ (#DC2626)
Text: Xám đậm (#374151)
```

---

## 📋 **SLIDE 11: KẾT QUẢ ĐẠT ĐƯỢC**

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  ✅ THÀNH TỰU DỰ ÁN                                    │
│                                                         │
│  ┌─────────────────┐  ┌─────────────────┐              │
│  │ 🎯 Hoàn Thành   │  │ 📈 Metrics      │              │
│  │                 │  │                 │              │
│  │ • Full-stack    │  │ • 95% test      │              │
│  │   application   │  │   coverage      │              │
│  │ • Advanced ML   │  │ • < 200ms API   │              │
│  │   engine        │  │   response      │              │
│  │ • Comprehensive │  │ • 99.9% uptime  │              │
│  │   admin system  │  │ • Scalable      │              │
│  │ • Performance   │  │   architecture  │              │
│  │   optimization  │  │                 │              │
│  └─────────────────┘  └─────────────────┘              │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 🏆 Achievements                                 │   │
│  │                                                │   │
│  │ • ✅ Complete recommendation engine            │   │
│  │ • ✅ Real-time content moderation              │   │
│  │ • ✅ Multi-language support                    │   │
│  │ • ✅ Advanced analytics dashboard              │   │
│  │ • ✅ Scalable microservices architecture       │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘

Background: Xám nhạt (#F9FAFB)
Headers: Đỏ (#DC2626)
Success boxes: Border đỏ (#DC2626), Background trắng (#FFFFFF)
Checkmarks: Đỏ (#DC2626)
Metrics: Đỏ (#DC2626)
Text: Xám đậm (#374151)
```

---

## 📋 **SLIDE 12: ROADMAP TƯƠNG LAI**

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  🚀 KẾ HOẠCH PHÁT TRIỂN                                │
│                                                         │
│  ┌─────────────────┐  ┌─────────────────┐              │
│  │ Phase 1         │  │ Phase 2         │              │
│  │ (3 tháng)       │  │ (6 tháng)       │              │
│  │                 │  │                 │              │
│  │ 📱 Mobile app   │  │ 🎥 Video        │              │
│  │ 🤖 Advanced ML  │  │   streaming     │              │
│  │ 👥 Social       │  │ 🥽 AR/VR        │              │
│  │   features      │  │   experiences   │              │
│  │                 │  │ ⛓️ Blockchain   │              │
│  └─────────────────┘  └─────────────────┘              │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Phase 3 (12 tháng)                              │   │
│  │                                                │   │
│  │ 🌍 International expansion                      │   │
│  │ 🏢 Enterprise solutions                         │   │
│  │ 🤝 AI research partnerships                     │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 🎯 Vision: Trở thành platform khuyến nghị      │   │
│  │    phim hàng đầu Việt Nam                       │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘

Background: Trắng (#FFFFFF)
Headers: Đỏ (#DC2626)
Phase boxes: Border đỏ (#DC2626), Background xám nhạt (#F3F4F6)
Timeline: Đỏ gradient (#DC2626 → #B91C1C)
Icons: Đỏ (#DC2626)
Text: Xám đậm (#374151)
```

---

## 📋 **SLIDE 13: KẾT LUẬN**

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  🎯 TỔNG KẾT                                          │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ ✅ THÀNH CÔNG                                    │   │
│  │                                                │   │
│  │ • Xây dựng hệ thống hoàn chỉnh                 │   │
│  │ • Giải pháp thực tế cho ngành giải trí         │   │
│  │ • Tiềm năng thương mại hóa cao                 │   │
│  │ • Đóng góp nghiên cứu ứng dụng AI/ML           │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 🌟 GIÁ TRỊ MANG LẠI                             │   │
│  │                                                │   │
│  │ • Cá nhân hóa trải nghiệm người dùng           │   │
│  │ • Tăng hiệu quả kinh doanh                     │   │
│  │ • Giải quyết vấn đề thông tin quá tải          │   │
│  │ • Tạo cộng đồng yêu thích phim ảnh             │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 🚀 TƯƠNG LAI                                     │   │
│  │                                                │   │
│  • Mobile app development                          │   │
│  • International expansion                         │   │
│  • Enterprise solutions                            │   │
│  • AI research partnerships                        │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘

Background: Gradient đỏ sang xám (#DC2626 → #1F2937)
Headers: Trắng (#FFFFFF)
Content boxes: Border trắng nhạt, Background xám đậm (#374151)
Text: Trắng (#FFFFFF)
```

---

## 📋 **SLIDE 14: Q&A**

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  ❓ CÂU HỎI & THẢO LUẬN                                │
│                                                         │
│                                                         │
│                    🎬 MOVIE MATE v2                    │
│                                                         │
│                                                         │
│  📧 Contact: [email]                                   │
│  🌐 Website: [website]                                 │
│  📱 GitHub: [repository]                               │
│  🎯 Demo: [demo link]                                  │
│                                                         │
│                                                         │
│  Cảm ơn bạn đã lắng nghe!                              │
│                                                         │
└─────────────────────────────────────────────────────────┘

Background: Gradient đỏ sang xám (#DC2626 → #1F2937)
Text: Trắng (#FFFFFF)
Contact info: Đỏ nhạt (#FEE2E2)
```

---

## 🎨 **HƯỚNG DẪN CANVA**

### **1. Color Palette Setup**

```
Primary Red: #DC2626
Secondary Red: #B91C1C
Light Red: #FEE2E2
Dark Gray: #1F2937
Medium Gray: #6B7280
Light Gray: #F3F4F6
White: #FFFFFF
```

### **2. Typography**

- **Headers**: Inter Bold, 36px, #DC2626
- **Subheaders**: Inter Semi-bold, 24px, #4B5563
- **Body Text**: Inter Regular, 16px, #6B7280
- **Captions**: Inter Light, 14px, #9CA3AF

### **3. Layout Elements**

- **Margins**: 40px uniform
- **Spacing**: 20px between elements
- **Border Radius**: 8px for boxes
- **Shadows**: Subtle gray shadows (#E5E7EB)

### **4. Icons & Graphics**

- **Icons**: Lucide React style, #DC2626
- **Charts**: Red gradient (#DC2626 → #B91C1C)
- **Progress bars**: Red (#DC2626)
- **Accent elements**: Light red (#FEE2E2)

---

## 📱 **RESPONSIVE ADAPTATIONS**

### **Desktop (16:9)**

- Full layout với tất cả elements
- Multiple columns
- Detailed charts

### **Tablet (4:3)**

- Simplified layout
- Larger text
- Fewer elements per slide

### **Mobile (9:16)**

- Single column
- Minimal text
- Focus on key points

---

Template này sẽ tạo ra một bài thuyết trình chuyên nghiệp, nhất quán với brand colors của bạn và dễ dàng customize trong Canva! 🎨✨
