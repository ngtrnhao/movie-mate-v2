# CHƯƠNG 1: GIỚI THIỆU TỔNG QUAN VÀ LÝ DO LỰA CHỌN ĐỀ TÀI

## 1.1. GIỚI THIỆU TỔNG QUAN

### 1.1.1. Bối cảnh nghiên cứu

Trong thời đại công nghệ số hiện nay, ngành công nghiệp điện ảnh đã có những bước phát triển vượt bậc với hàng trăm nghìn bộ phim được sản xuất mỗi năm. Theo thống kê của Statista (2023), có hơn 1.2 triệu bộ phim được sản xuất trên toàn thế giới, với hàng nghìn bộ phim mới được phát hành mỗi năm. Trước khối lượng nội dung khổng lồ này, người dùng thường gặp khó khăn trong việc:

- **Tìm kiếm phim phù hợp**: Với hàng nghìn bộ phim có sẵn, việc tìm ra những bộ phim phù hợp với sở thích cá nhân trở thành một thách thức lớn
- **Đánh giá chất lượng phim**: Thiếu thông tin đáng tin cậy về chất lượng phim trước khi quyết định xem
- **Khám phá phim mới**: Khó khăn trong việc phát hiện những bộ phim hay nhưng ít được biết đến
- **Quản lý danh sách phim**: Không có công cụ hiệu quả để lưu trữ và quản lý danh sách phim yêu thích

### 1.1.2. Vấn đề nghiên cứu

Mặc dù có nhiều nền tảng thông tin phim hiện có (như IMDB, Rotten Tomatoes, Letterboxd), nhưng hầu hết đều tồn tại những hạn chế sau:

**Về trải nghiệm người dùng:**

- Giao diện tìm kiếm và lọc phim phức tạp, khó sử dụng
- Thiếu tính năng gợi ý phim thông minh dựa trên sở thích cá nhân
- Hệ thống đánh giá và review chưa được tối ưu hóa cho người dùng Việt Nam
- Không có tính năng tương tác và chia sẻ với cộng đồng người dùng

**Về công nghệ:**

- Thuật toán gợi ý phim đơn giản, chưa tận dụng được dữ liệu người dùng
- Không có hệ thống phân tích hành vi người dùng để cải thiện gợi ý
- Thiếu tích hợp với các nguồn dữ liệu phim đa dạng
- Hiệu năng hệ thống chưa được tối ưu hóa cho lượng dữ liệu lớn

**Về nội dung:**

- Thông tin phim thiếu chi tiết và cập nhật
- Không có hệ thống phân loại và gắn thẻ thông minh
- Thiếu tính năng phát hiện spoiler trong review
- Chưa có cơ chế kiểm duyệt nội dung hiệu quả

### 1.1.3. Mục tiêu nghiên cứu

Để giải quyết những vấn đề trên, đề tài nghiên cứu này hướng đến các mục tiêu chính sau:

**Mục tiêu chính:**

- Xây dựng hệ thống gợi ý phim thông minh dựa trên thuật toán Machine Learning
- Phát triển nền tảng web tương tác với hệ thống đánh giá và review phim
- Tích hợp đa dạng nguồn dữ liệu phim để cung cấp thông tin chi tiết và chính xác

**Mục tiêu cụ thể:**

1. **Hệ thống gợi ý phim thông minh:**

   - Triển khai thuật toán Collaborative Filtering để phân tích hành vi người dùng
   - Áp dụng Content-based Filtering dựa trên đặc điểm phim (thể loại, diễn viên, đạo diễn)
   - Xây dựng thuật toán Demographic Filtering dựa trên thông tin cá nhân người dùng
   - Phát triển thuật toán Hybrid kết hợp nhiều phương pháp gợi ý
   - Tối ưu hóa hiệu năng hệ thống gợi ý với cơ chế caching và background processing

2. **Nền tảng web tương tác:**

   - Thiết kế giao diện người dùng hiện đại và responsive
   - Xây dựng hệ thống đăng ký, đăng nhập và quản lý tài khoản
   - Phát triển tính năng đánh giá phim (rating) với hệ thống sao
   - Xây dựng hệ thống review phim với tính năng tương tác (like, reply)
   - Tích hợp hệ thống thanh toán và gói dịch vụ premium (Basic, Standard, VIP)

3. **Quản lý nội dung thông minh:**
   - Tích hợp dữ liệu từ nhiều nguồn (IMDB, TMDB, MovieLens)
   - Xây dựng hệ thống kiểm duyệt nội dung tự động
   - Phát triển tính năng phát hiện spoiler trong review bằng AI
   - Tối ưu hóa hiệu năng tìm kiếm và lọc phim với Elasticsearch
   - Xây dựng hệ thống quản lý nội dung cho admin và moderator

## 1.2. LÝ DO LỰA CHỌN ĐỀ TÀI

### 1.2.1. Tính thực tiễn và ứng dụng cao

**Nhu cầu thị trường:**

- Thị trường thông tin và đánh giá phim đang phát triển mạnh mẽ
- Người dùng Việt Nam ngày càng quan tâm đến việc tìm hiểu và đánh giá phim
- Nhu cầu về các nền tảng gợi ý nội dung thông minh ngày càng tăng
- Thiếu các nền tảng thông tin phim được tối ưu hóa cho người dùng Việt Nam

**Giá trị kinh tế:**

- Tiềm năng thương mại hóa sản phẩm cao thông qua gói dịch vụ premium
- Có thể mở rộng sang các lĩnh vực giải trí khác (nhạc, sách, game)
- Tạo cơ hội việc làm trong lĩnh vực AI/ML và phát triển web
- Có thể trở thành nền tảng cộng đồng chia sẻ và thảo luận về phim

### 1.2.2. Tính khoa học và kỹ thuật

**Thách thức kỹ thuật:**

- Xử lý và phân tích dữ liệu lớn từ nhiều nguồn khác nhau (IMDB, TMDB, MovieLens)
- Tối ưu hóa thuật toán gợi ý để đảm bảo độ chính xác và hiệu năng
- Xây dựng kiến trúc hệ thống có khả năng mở rộng cao
- Tích hợp nhiều công nghệ hiện đại (AI/ML, Web Development, Database, Search Engine)
- Xử lý bài toán phát hiện spoiler trong review bằng Machine Learning

**Đóng góp khoa học:**

- Nghiên cứu và cải tiến thuật toán gợi ý phim kết hợp nhiều phương pháp
- Phát triển phương pháp kết hợp nhiều nguồn dữ liệu phim
- Đề xuất giải pháp tối ưu hóa hiệu năng hệ thống gợi ý
- Nghiên cứu ứng dụng AI trong việc phát hiện spoiler

### 1.2.3. Phù hợp với chuyên ngành và định hướng phát triển

**Liên quan đến chuyên ngành:**

- Ứng dụng kiến thức về Cơ sở dữ liệu và Hệ thống thông tin
- Vận dụng các thuật toán Machine Learning và Data Mining
- Thực hành phát triển ứng dụng web với các công nghệ hiện đại (Django, React)
- Tích hợp kiến thức về Kiến trúc phần mềm và Thiết kế hệ thống
- Áp dụng kiến thức về Search Engine và Information Retrieval

**Định hướng tương lai:**

- Phát triển kỹ năng trong lĩnh vực AI/ML đang hot
- Có cơ hội tham gia các dự án lớn về Recommendation System
- Mở rộng kiến thức về Big Data và Cloud Computing
- Chuẩn bị cho việc học tập và nghiên cứu sau đại học
- Có thể phát triển thành startup hoặc sản phẩm thương mại

### 1.2.4. Tính khả thi và nguồn lực

**Tính khả thi về mặt kỹ thuật:**

- Có sẵn các công cụ và thư viện hỗ trợ phát triển (Django, React, scikit-learn)
- Dữ liệu phim có sẵn từ nhiều nguồn mở (IMDB, TMDB, MovieLens)
- Có thể triển khai và test trên môi trường thực tế
- Có sẵn các thuật toán gợi ý đã được nghiên cứu và tối ưu

**Nguồn lực sẵn có:**

- Kiến thức nền tảng về lập trình Python và JavaScript
- Kinh nghiệm với các công nghệ web development (Django, React)
- Hiểu biết về cơ sở dữ liệu và thuật toán Machine Learning
- Hỗ trợ từ giảng viên hướng dẫn và cộng đồng open source

### 1.2.5. Đóng góp xã hội

**Cải thiện trải nghiệm người dùng:**

- Giúp người dùng dễ dàng tìm kiếm phim phù hợp với sở thích
- Tiết kiệm thời gian trong việc lựa chọn nội dung giải trí
- Cung cấp thông tin đáng tin cậy về chất lượng phim
- Tạo cộng đồng chia sẻ và thảo luận về phim

**Thúc đẩy phát triển công nghệ:**

- Góp phần phát triển các ứng dụng AI/ML trong thực tế
- Tạo tiền đề cho các nghiên cứu về Recommendation System
- Khuyến khích việc áp dụng công nghệ mới trong lĩnh vực giải trí
- Đóng góp vào cộng đồng open source

## 1.3. PHẠM VI VÀ GIỚI HẠN NGHIÊN CỨU

### 1.3.1. Phạm vi nghiên cứu

**Về nội dung:**

- Tập trung vào lĩnh vực phim điện ảnh và phim truyền hình
- Bao gồm các thể loại phim phổ biến (hành động, tình cảm, kinh dị, hài, v.v.)
- Hỗ trợ đa ngôn ngữ (tiếng Anh và tiếng Việt)
- Tích hợp thông tin từ các nguồn dữ liệu phim uy tín

**Về đối tượng người dùng:**

- Người dùng cá nhân có nhu cầu tìm hiểu và đánh giá phim
- Các nhóm tuổi từ 16-50 tuổi
- Người dùng có kiến thức cơ bản về công nghệ
- Admin và moderator quản lý nội dung

**Về công nghệ:**

- Phát triển ứng dụng web responsive
- Tích hợp với các API phim có sẵn (TMDB, IMDB)
- Triển khai trên nền tảng cloud (Render, Vercel)
- Sử dụng các thuật toán Machine Learning cơ bản

### 1.3.2. Giới hạn nghiên cứu

**Về dữ liệu:**

- Chỉ sử dụng dữ liệu phim có sẵn từ các nguồn mở
- Không bao gồm nội dung phim có bản quyền
- Giới hạn về số lượng phim trong giai đoạn thử nghiệm
- Chưa tích hợp với tất cả các nguồn dữ liệu phim trên thế giới

**Về thuật toán:**

- Tập trung vào các thuật toán gợi ý cơ bản và phổ biến
- Chưa áp dụng các kỹ thuật Deep Learning phức tạp
- Giới hạn về khả năng xử lý dữ liệu lớn
- Thuật toán phát hiện spoiler còn ở mức cơ bản

**Về tính năng:**

- Không bao gồm tính năng streaming video
- Không có tính năng chat real-time
- Giới hạn về tính năng social networking
- Chưa có tính năng mobile app

## 1.4. PHƯƠNG PHÁP NGHIÊN CỨU

### 1.4.1. Phương pháp nghiên cứu lý thuyết

**Nghiên cứu tài liệu:**

- Thu thập và phân tích tài liệu về Recommendation System
- Nghiên cứu các thuật toán Machine Learning liên quan (Collaborative Filtering, Content-based Filtering)
- Tìm hiểu về kiến trúc hệ thống và công nghệ web
- Nghiên cứu về Natural Language Processing cho việc phát hiện spoiler

**Phân tích và so sánh:**

- So sánh các phương pháp gợi ý khác nhau
- Đánh giá ưu nhược điểm của từng thuật toán
- Phân tích các nền tảng thông tin phim hiện có
- Nghiên cứu các giải pháp tối ưu hóa hiệu năng

### 1.4.2. Phương pháp nghiên cứu thực nghiệm

**Thiết kế và phát triển:**

- Thiết kế kiến trúc hệ thống tổng thể
- Phát triển từng module chức năng (user management, movie management, recommendation system)
- Tích hợp và test hệ thống
- Triển khai và monitor hệ thống trên production

**Đánh giá và tối ưu:**

- Đánh giá hiệu năng thuật toán gợi ý
- Tối ưu hóa hiệu năng hệ thống
- Thu thập phản hồi từ người dùng
- Cải thiện thuật toán dựa trên feedback

### 1.4.3. Phương pháp đánh giá

**Đánh giá định lượng:**

- Đo lường độ chính xác của thuật toán gợi ý (Precision, Recall, F1-score)
- Đánh giá hiệu năng hệ thống (thời gian phản hồi, throughput)
- Phân tích dữ liệu sử dụng và tương tác người dùng
- Đánh giá hiệu năng tìm kiếm với Elasticsearch

**Đánh giá định tính:**

- Thu thập phản hồi từ người dùng thử nghiệm
- Đánh giá trải nghiệm người dùng (UX/UI)
- Phân tích tính khả dụng và tính hữu ích của hệ thống
- Đánh giá chất lượng hệ thống kiểm duyệt nội dung

## 1.5. CẤU TRÚC LUẬN VĂN

Luận văn được tổ chức thành các chương chính sau:

**Chương 1: Giới thiệu tổng quan và lý do lựa chọn đề tài**

- Giới thiệu bối cảnh và vấn đề nghiên cứu
- Mục tiêu và phạm vi nghiên cứu
- Lý do lựa chọn đề tài và phương pháp nghiên cứu

**Chương 2: Cơ sở lý thuyết**

- Tổng quan về Recommendation System
- Các thuật toán Machine Learning liên quan
- Công nghệ và framework sử dụng (Django, React, Elasticsearch)

**Chương 3: Phân tích và thiết kế hệ thống**

- Phân tích yêu cầu và use case
- Thiết kế kiến trúc hệ thống
- Thiết kế cơ sở dữ liệu và giao diện

**Chương 4: Triển khai và thực nghiệm**

- Triển khai các module chức năng
- Tích hợp và test hệ thống
- Đánh giá hiệu năng và kết quả

**Chương 5: Kết luận và hướng phát triển**

- Tổng kết kết quả đạt được
- Đánh giá ưu nhược điểm
- Đề xuất hướng phát triển tương lai

---

_Chương này đã trình bày tổng quan về đề tài nghiên cứu, bao gồm bối cảnh, vấn đề nghiên cứu, mục tiêu và lý do lựa chọn đề tài. Các nội dung này sẽ là cơ sở để triển khai các chương tiếp theo của luận văn._
