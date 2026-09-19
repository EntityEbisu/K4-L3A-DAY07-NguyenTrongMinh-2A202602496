# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** G21
**Ngày:** 19/09/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Học phí và quy định thu nộp học phí của các trường đại học tại Việt Nam.

**Tại sao nhóm chọn chủ đề này?**
> Chúng tôi chọn chủ đề học phí vì đây là vấn đề có tính thời sự, rõ ràng và có nhiều nguồn chính thức. Bộ dữ liệu bao gồm các quy định của trường, thông báo năm học và các mức thu theo quy định, nên rất phù hợp để so sánh hiệu quả của retrieval và filter metadata.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------------|----------------------|----------|-----------------|
| 1 | Quy định thu nộp học phí đối với sinh viên FTU | https://khoadaotaotructuyen.ftu.edu.vn/van-ban-bieu-mau/quy-dinh-ve-thu-nop-hoc-phi-doi-voi-sinh-vien/ | 2026-09-19 / not-stated | ~3.0k | `doc_id`, `title`, `source_url`, `retrieved_at`, `document_version`, `audience`, `department`, `category`, `language` |
| 2 | Quy định thu học phí ĐHKHTN | https://bio.hus.vnu.edu.vn/quy-dinh-ve-viec-thu-hoc-phi-dao-tao-cac-bac-hoc-cua-truong-dhkhtn/ | 2026-09-19 / not-stated | ~8.5k | `doc_id`, `title`, `source_url`, `retrieved_at`, `document_version`, `audience`, `department`, `category`, `language` |
| 3 | Thông báo thu học phí VNUA 2026 | https://vnua.edu.vn/thong-bao/thay-doi-lich-thu-tien-hoc-phi-dot-1-hoc-ki-i-nam-hoc-2026-2027-doi-voi-sinh-vien-58812 | 2026-09-19 / 2026-07-18 | ~2.7k | `doc_id`, `title`, `source_url`, `retrieved_at`, `document_version`, `audience`, `department`, `category`, `language` |
| 4 | Học phí HUST 2026-2027 | https://huongnghiep.hocmai.vn/hoc-phi-dai-hoc-bach-khoa-ha-noi-2026-2027-chi-tiet-muc-thu-moi-nhat-cho-tung-chuong-trinh-dao-tao | 2026-09-19 / 2026-08-03 | ~8.0k | `doc_id`, `title`, `source_url`, `retrieved_at`, `document_version`, `audience`, `department`, `category`, `language` |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | string | `hoc-phi-hust-2026` | Dùng để định danh ổn định mỗi tài liệu và thực hiện xóa/định tuyến đúng đối tượng |
| `title` | string | `Học phí Đại học Bách khoa Hà Nội 2026-2027` | Dễ nhận biết chủ đề của tài liệu khi nhìn ra top-k |
| `source_url` | string | URL từ website chính thức | Cho phép kiểm tra nguồn gốc và xác nhận độ tin cậy |
| `retrieved_at` | date | `2026-09-19` | Cho biết ngày thu thập dữ liệu |
| `document_version` | string | `2026-08-03` hoặc `not-stated` | Dễ so sánh phiên bản và tính hiệu lực |
| `audience` | string | `student` / `all` | Quan trọng nhất cho filter metadata trong retrieval |
| `department` | string | `finance` / `academic-affairs` | Phân nhóm theo mảng quy định và hỗ trợ lọc theo miền |
| `category` | string | `tuition` | Nhóm tài liệu theo chủ đề chính |
| `language` | string | `vi` | Khởi tạo chuẩn hóa cho đa ngôn ngữ |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Dùng `ChunkingStrategyComparator().compare()` trên nội dung của 2-3 tài liệu chính trong corpus (HUST, HUS, VNUA):

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| `hoc-phi-hust-2026.md` | `fixed_size` | cao | trung bình | Có, nhưng dễ tách vô nghĩa nếu không chồng chéo phù hợp |
| `hoc-phi-hust-2026.md` | `by_sentences` | vừa phải | ổn | Có, nhưng câu dài hoặc nhiều tiêu đề khiến bị phân mảnh |
| `hoc-phi-hust-2026.md` | `recursive` | cân bằng nhất | ổn | Có, giữ tốt cấu trúc nếu có heading và section |

### Chiến lược của từng thành viên

**Thành viên 1 — Nguyễn Trọng Minh**
- **Loại chiến lược:** Recursive
- **Mô tả & lý do chọn cho chủ đề này:** Chúng tôi sử dụng recursive chunking vì các tài liệu quy định đều có heading và section rõ ràng. Cách này giữ được ngữ cảnh của từng mục, đặc biệt với các phần như “Mức thu”, “Phương thức thu”, “Học bổng”.
- **Code snippet (nếu custom):**
```python
from src.chunking import RecursiveChunker
chunks = RecursiveChunker(chunk_size=500).chunk(text)
```

**Thành viên 2 — Lê Mạnh Cường**
- **Loại chiến lược:** Sentence
- **Mô tả & lý do chọn:** Sentence chunking phù hợp với thông tin quy định có dạng câu ngắn và đoạn ngắn. Nó dễ đọc hơn, và khi truy xuất sẽ ít rơi vào kết quả quá dài hoặc bị lẫn do tiêu đề trang web.
- **Code snippet (nếu custom):**
```python
from src.chunking import SentenceChunker
chunks = SentenceChunker(max_sentences_per_chunk=3).chunk(text)
```

**Thành viên 3 — Trần Quốc Khánh**
- **Loại chiến lược:** Fixed-size
- **Mô tả & lý do chọn:** Fixed-size dùng khi cần đảm bảo chunk có độ dài đồng đều, dễ so sánh và dễ triển khai. Ưu điểm là phần code đơn giản, nhưng cần overlap tốt để không làm mất dữ liệu ở ranh giới.
- **Code snippet (nếu custom):**
```python
from src.chunking import FixedSizeChunker
chunks = FixedSizeChunker(chunk_size=500, overlap=50).chunk(text)
```

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Nguyễn Trọng Minh | Recursive | 8.5 | Giữ được ngữ cảnh, phù hợp tài liệu có heading | Có thể tạo chunk dài nếu phần section lớn |
| Lê Mạnh Cường | Sentence | 7.5 | Dễ đọc, phù hợp câu định nghĩa | Có thể tách quá mảnh và mất liên kết |
| Trần Quốc Khánh | Fixed-size | 7.0 | Dễ triền khai, đồng đều | Dễ mất thông tin ở biên và khiến retrieval lẫn mục |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> Với corpus học phí, recursive chunking là tối ưu nhất vì phần lớn tài liệu được tổ chức theo tiêu đề và section có tính ngữ nghĩa rõ. Fixed-size tiện cho kiểm soát kích thước nhưng dễ làm mất context ở phần đầu/cuối của section; sentence chunking thì quá mảnh nếu nội dung dài và nhiều câu liên quan. Vì vậy, recursive là phương án cân bằng nhất giữa “độ dài”, “đúng ngữ cảnh” và “độ rõ ràng của thông tin”.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Học phí chương trình chuẩn của HUST năm 2026-2027 dao động trong khoảng nào? | 28 đến 40 triệu đồng/năm | `hoc-phi-hust-2026.md` |
| 2 | Nhóm chương trình Elitech của HUST thu học phí theo mức nào? | 35 đến 68 triệu đồng/năm | `hoc-phi-hust-2026.md` |
| 3 | Các chương trình tài năng và quốc tế của HUST tính học phí theo năm hay theo kỳ? | Theo kỳ | `hoc-phi-hust-2026.md` |
| 4 | Theo quy định của Trường ĐHKHTN, học phí môn học được tính như thế nào? | 165.000 đ/1 tín chỉ x số tín chỉ x hệ số môn học | `hus-quy-dinh-thu-hoc-phi.md` |
| 5 | Học phí của chương trình chuẩn tại HUST có tăng tối đa bao nhiêu so với năm trước? | Giữ nguyên hoặc tăng không quá 5 triệu đồng/năm | `hoc-phi-hust-2026.md` |

### Tổng hợp chất lượng truy xuất của nhóm

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Học phí chương trình chuẩn của HUST ... | Recursive | Có | Filter `audience=student` giúp giảm nhiễu từ các trường khác |
| 2 | Elitech của HUST ... | Recursive | Có | Trả lời rõ, nằm trong phần “Chương trình Elitech” |
| 3 | Theo năm hay theo kỳ? | Recursive | Có | Dùng metadata filter giúp tránh lẫn giữa tài liệu học phí trường khác |
| 4 | Công thức học phí ĐHKHTN | Recursive | Có | Filter `audience=all` giúp chọn đúng tài liệu chính |
| 5 | Tăng tối đa bao nhiêu? | Recursive | Có | Nhạy cảm với từ khóa “tăng”, cần ngữ cảnh rõ |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Metadata filter có ích rõ rệt với các câu hỏi cần chọn đúng đối tượng, ví dụ câu 1 và câu 5. Khi không lọc, các tài liệu từ trường khác có từ khóa tương tự như “học phí”, “sinh viên”, “thu học phí” cũng xuất hiện và làm tăng nhiễu. Với `audience=student`, retrieval tập trung vào các tài liệu dành cho sinh viên, giúp kết quả phù hợp hơn với câu hỏi.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> 1. Tài liệu học phí có nhiều phần lặp lại ở menu, footer và phần quảng cáo; cần tách frontmatter và giữ phần nội dung có giá trị thật.  
> 2. Filter `audience` là yếu tố quyết định cho câu hỏi có tính đối tượng.  
> 3. Recursive chunking giữ tốt cấu trúc section, phù hợp với văn bản quy định theo mục.

**Bài học rút ra khi so sánh trong nhóm:**
> Chúng tôi thấy cùng bộ tài liệu nhưng chiến lược khác nhau cho kết quả truy xuất khác nhau. Recursive chunking giữ được chủ đề và ngữ cảnh tốt hơn, trong khi fixed-size dễ tạo ra chunk “rời rạc”, và sentence chunking có thể quá mảnh. Sự khác biệt này làm ảnh hưởng trực tiếp đến chất lượng top-k và độ ổn định của câu trả lời.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Nếu làm lại, nhóm sẽ ưu tiên sắp xếp nội dung theo section rõ ràng và giữ đúng `audience`, đồng thời lọc bỏ phần menu/footer bằng tay. Ngoài ra, chúng tôi sẽ thêm các query có mục tiêu kiểm tra filter để xác định chân dung thật của bộ dữ liệu trước khi chạy benchmark.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 9 / 10 |
| Thiết kế chiến lược (Strategy Design) | 13 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 9 / 10 |
| Thuyết trình (Demo) | 4 / 5 |
| **Tổng phần nhóm** | **35 / 40** |
