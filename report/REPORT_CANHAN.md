# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** [Nguyễn Trọng Minh]
**Nhóm:** G21
**Ngày:** 19/09/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Khi hai vector có hướng gần giống nhau, cosine similarity gần 1. Với text embedding, điều này có nghĩa hai câu có cùng ý nghĩa dù từ vựng khác nhau vẫn có thể được xem là gần nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: “Học phí chương trình chuẩn HUST năm 2026-2027 dao động từ 28 đến 40 triệu đồng/năm.”
- Câu B: “Năm học 2026-2027, mức học phí chương trình chuẩn của HUST rơi vào khoảng 28-40 triệu đồng mỗi năm.”
- Tại sao tương đồng: Hai câu dùng từ khóa tương ứng nhưng không hoàn toàn giống nhau; embedding hiểu ý nghĩa chứ không chỉ khớp chữ.

**Ví dụ có độ tương tự THẤP:**
- Câu A: “Học phí HUST tăng thêm 5 triệu đồng/năm cho chương trình chuẩn.”
- Câu B: “Khoa học dữ liệu và trí tuệ nhân tạo đang là ngành tuyển sinh nóng trong năm nay.”
- Tại sao khác: Chủ đề hoàn toàn khác, dù có từ “học”, “năm” nhưng không cùng nghĩa.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Vì text embeddings là vector hướng trong không gian nhiều chiều, không phải độ dài tuyệt đối. Cosine dựa trên góc giữa hai vector, nên nó ổn hơn khi câu có độ dài khác nhau nhưng ý nghĩa tương tự.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Tính theo công thức: ceil((10,000 - 50) / (500 - 50)) = ceil(9,950 / 450) = ceil(22.11) = 23 chunk.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Với overlap = 100, bước di chuyển là 400, nên số chunk khoảng ceil(9,900 / 400) = 25. Overlap lớn giúp giữ ngữ cảnh ở ranh giới chunk, nhưng tốn nhiều dữ liệu lặp lại và làm tăng số chunk.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Tôi dùng regex tách theo vị trí sau dấu câu: `(?<=[.!?])\s+`, rồi gom từng nhóm câu theo `max_sentences_per_chunk`. Điều này giữ được dấu câu và tránh làm mất ngữ nghĩa. Với edge case, tôi kiểm tra `text.strip()` rỗng và không cho phép split gây crash.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán hoạt động theo kiểu đệ quy theo thứ tự separator ưu tiên: `\n\n`, `\n`, `. `, ` `, `""`. Khi một mảnh vẫn quá dài, tôi tiếp tục cắt ở separator nhỏ hơn và cuối cùng merge lại các phần nhỏ để tránh chunk quá ngắn và không có ngữ cảnh.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Tôi lưu từng chunk dưới dạng `Document` có `id`, `content`, `metadata` rồi sinh embedding cho nội dung bằng hàm được inject. Search tính dot product giữa query embedding và từng record embedding, sau đó sắp xếp theo score giảm dần.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Filter được thực hiện trước khi tính similarity để tránh các tài liệu không phù hợp chiếm slot top-k. Với `delete_document`, tôi lọc toàn bộ các record có `metadata['doc_id']` khớp với doc_id cần xóa, trả về `True` nếu xóa thành công.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Tôi xây prompt có phần “Context” gồm các chunk đã được đánh số `[1]`, `[2]`, `[3]`. Sau đó yêu cầu model trả lời chỉ dựa trên ngữ cảnh đó. Cách này giúp truy vết nguồn rõ ràng hơn và ngăn model bịa thông tin ngoài dữ liệu được cung cấp.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```text
============================= test session starts =============================
...
============================= 42 passed in 0.13s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Học phí chương trình chuẩn HUST | Học phí chương trình chuẩn HUST năm 2026-2027 | cao | cao | Có |
| 2 | Học phí trường ĐHKHTN | Mức học phí môn học theo tín chỉ | cao | cao | Có |
| 3 | Học phí của HUST | Lịch thi tốt nghiệp đại học | thấp | thấp | Có |
| 4 | Mức thu học phí từng khoa | Mức học phí năm trước và hiện tại | cao | cao | Có |
| 5 | Quy định thu học phí sinh viên | Quy định về ký túc xá | thấp | thấp | Có |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Kết quả bất ngờ nhất là các câu có từ khóa tương tự nhưng khác chủ đề thường vẫn thấp. Điều này cho thấy embedding không chỉ dựa vào từ khớp đơn giản; nó hiểu hướng ý nghĩa của văn bản và cho thấy độ quan trọng của ngữ cảnh.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Học phí chương trình chuẩn HUST | Mức học phí chương trình chuẩn 28-40 triệu/năm | ~0.26 | Có | 28-40 triệu đồng/năm |
| 2 | Elitech HUST | Chương trình Elitech 35-68 triệu/năm | ~0.26 | Có | 35-68 triệu đồng/năm |
| 3 | Tính theo năm hay theo kỳ? | Chương trình tài năng/quốc tế tính theo kỳ | ~0.27 | Có | Theo kỳ |
| 4 | Công thức học phí ĐHKHTN | 165.000 đ/1 tín chỉ x số tín chỉ x hệ số môn học | ~0.23 | Có | 165.000 đ/1 tín chỉ x số tín chỉ x hệ số môn học |
| 5 | Tăng tối đa bao nhiêu? | Giữ nguyên hoặc tăng <= 5 triệu | ~0.30 | Có | Giữ nguyên hoặc tăng không quá 5 triệu đồng/năm |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Việc filter metadata giúp giảm nhiễu rất mạnh nếu query liên quan đến đối tượng cụ thể. Đồng thời, đoạn văn bản có tiêu đề rõ ràng và section hợp lý sẽ tốt hơn nhiều so với văn bản thô có menu, footer và quảng cáo lặp lại.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 9 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương sim (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **59 / 60** |
