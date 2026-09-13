# 📊 BÁO CÁO THU HOẠCH NGHIỆM THU BÀI LAB 3 (BƯỚC 3 — SUBMISSION ARTIFACT)

> **Họ và Tên Học viên:** Lê Việt Hoàng
> **Mã Sinh Viên / Mã Học viên:** 2A202602596 
> **Chủ đề Lựa chọn:** Trợ lý Tuyển dụng & Sàng lọc CV: Tra cứu tiêu chí tuyển dụng vị trí và gửi thông báo lịch phỏng vấn.  

---

## 1. BẢNG CHẤM ĐIỂM AGENTIC FIT SCORING MATRIX (ĐÁNH GIÁ CHỦ ĐỀ)

| Tiêu chí Đánh giá | Mức độ (1 - 5) | Giải trình chi tiết lý do chọn điểm |
| :--- | :---: | :--- |
| **1. Multi-step Reasoning** | 4 / 5 | Bài toán có yêu cầu chia nhỏ nhiều bước suy luận nối tiếp nhau không? |
| **2. Tool Interaction** | 5 / 5 | Hệ thống có cần kết nối với MCP Server / Cơ sở dữ liệu bên ngoài không? |
| **3. Dynamic Decision** | 4 / 5 | Bước tiếp theo có phụ thuộc vào kết quả quan sát bước trước không? |
| **4. Long Horizon Goal** | 4 / 5 | Hệ thống có phải giữ mục tiêu xuyên suốt qua nhiều lượt xử lý không? |
| **TỔNG ĐIỂM AGENTIC FIT** | ** 17 / 20** | *Nếu tổng điểm > 12/20: Bài toán rất phù hợp triển khai Agentic System.* |

Giải thích lý do chấm điểm như vậy:
Tiêu chí Đánh giá,Mức độ (1 - 5),Giải trình chi tiết lý do chọn điểm
1. Multi-step Reasoning,4 / 5,Cần thực hiện chuỗi suy luận logic gồm nhiều chặng: Phân tích JD → Trích xuất kỹ năng từ CV → Đối chiếu/chấm điểm lệch (Gap Analysis) → Quyết định Đạt/Không đạt → Đề xuất khung giờ phỏng vấn phù hợp.
2. Tool Interaction,5 / 5,"Phụ thuộc hoàn toàn vào hệ thống Tool/MCP Server: Đọc file CV (PDF/Docx), truy vấn cơ sở dữ liệu JD/Hồ sơ (Database/Vector DB), gọi API Lịch làm việc (Google Calendar/Outlook API) và API Gửi Email (SendGrid/Mailgun/SMTP)."
3. Dynamic Decision,4 / 5,Luồng xử lý rẽ nhánh linh hoạt dựa trên kết quả bước trước: Nếu CV thiếu thông tin quan trọng → Gọi tool gửi mail yêu cầu bổ sung; Nếu Đạt → Check lịch trống và gửi thư mời; Nếu Không đạt → Chuyển sang luồng gửi thư cảm ơn.
4. Long Horizon Goal,4 / 5,Mục tiêu cuối cùng là hoàn thành quy trình tuyển dụng cho ứng viên (từ ứng tuyển đến khi xác nhận lịch phỏng vấn). Agent phải duy trì state (trạng thái ứng viên) và ngữ cảnh qua nhiều lượt tương tác bất đồng bộ (Email reply/Chấp nhận lịch).
TỔNG ĐIỂM AGENTIC FIT,17 / 20,Kết luận: Rất phù hợp triển khai Agentic System. (Vượt xa mốc chuẩn 12/20)
---

## 2. TRÍCH XUẤT KẾT QUẢ WATERFALL TRACE LOG (SAU KHI CHẠY TEST SUITE TRÊN API THẬT)

> ⚠️ **YÊU CẦU NGHIỆM THU:** Mở tệp `.env` điền `GEMINI_API_KEY` (hoặc `OPENAI_API_KEY`) để kết nối LLM thật trước khi thực thi `python src/app.py --all`. Bài nộp chỉ dùng Mock Offline Provider sẽ không đạt điểm nghiệm thực tế.

> 🔎 **Nguồn log thật:** `python src/app.py --all` chạy trên **LLM thật (Google Gemini)**, SDK `google-genai` 2.23.0, model `gemini-3.5-flash`; **11/11 sự kiện trong `docs/trace_waterfall.json` đều sinh từ LLM API thật, 0 lần fallback Mock** (`⚠️ [Gemini API Warning]` = 0). Trích đoạn dưới đây là chuỗi ReAct 3 bước tiêu biểu của **TC04 (multi_step_reasoning)**: `job_criteria_query` → `send_interview_invitation` → `FINAL_ANSWER`.

```json
[
  {
    "step": 1,
    "query": "Tôi đang sàng lọc CV cho vị trí AI Engineer (mã vị trí JD-2026-AI01). Hãy tra cứu giúp tôi tiêu chí tuyển dụng của vị trí này, sau đó gửi thông báo lịch phỏng vấn cho ứng viên UV2026001 vào 09:30 ngày 18/09/2026.",
    "action_type": "TOOL_EXECUTION",
    "thought": "Gemini quyết định gọi công cụ 'job_criteria_query' với tham số: {\"job_id\": \"JD-2026-AI01\"}",
    "tool_name": "job_criteria_query",
    "arguments": {
      "job_id": "JD-2026-AI01"
    },
    "observation": {
      "status": "SUCCESS",
      "job_id": "JD-2026-AI01",
      "data": {
        "job_title": "AI Engineer",
        "department": "Khối Công nghệ & Dữ liệu",
        "level": "Junior/Middle",
        "required_skills": ["Python", "Machine Learning", "PyTorch/TensorFlow", "SQL"],
        "min_experience_years": 2,
        "education": "Tốt nghiệp Đại học ngành CNTT / Khoa học dữ liệu",
        "gpa_requirement": "GPA >= 3.0/4.0",
        "english_requirement": "IELTS 6.5+ hoặc tương đương",
        "hiring_manager": "TS. Nguyễn Văn A",
        "status": "Đang mở"
      }
    },
    "latency_ms": 2192.75
  },
  {
    "step": 2,
    "query": "Tôi đang sàng lọc CV cho vị trí AI Engineer (mã vị trí JD-2026-AI01). Hãy tra cứu giúp tôi tiêu chí tuyển dụng của vị trí này, sau đó gửi thông báo lịch phỏng vấn cho ứng viên UV2026001 vào 09:30 ngày 18/09/2026.",
    "action_type": "TOOL_EXECUTION",
    "thought": "Gemini quyết định gọi công cụ 'send_interview_invitation' với tham số: {\"candidate_id\": \"UV2026001\", \"datetime_str\": \"09:30 18/09/2026\", \"job_id\": \"JD-2026-AI01\", \"interviewer_name\": \"TS. Nguyễn Văn A\"}",
    "tool_name": "send_interview_invitation",
    "arguments": {
      "candidate_id": "UV2026001",
      "datetime_str": "09:30 18/09/2026",
      "job_id": "JD-2026-AI01",
      "interviewer_name": "TS. Nguyễn Văn A"
    },
    "observation": {
      "status": "SUCCESS",
      "invitation_id": "IV-UV2026001-JD-2026-AI01",
      "candidate_id": "UV2026001",
      "job_id": "JD-2026-AI01",
      "job_title": "AI Engineer",
      "datetime": "09:30 18/09/2026",
      "interviewer": "TS. Nguyễn Văn A",
      "message": "Đã gửi thông báo lịch phỏng vấn tới ứng viên UV2026001 cho vị trí AI Engineer (JD-2026-AI01) với TS. Nguyễn Văn A vào lúc 09:30 18/09/2026."
    },
    "latency_ms": 2301.67
  },
  {
    "step": 3,
    "query": "Tôi đang sàng lọc CV cho vị trí AI Engineer (mã vị trí JD-2026-AI01). Hãy tra cứu giúp tôi tiêu chí tuyển dụng của vị trí này, sau đó gửi thông báo lịch phỏng vấn cho ứng viên UV2026001 vào 09:30 ngày 18/09/2026.",
    "action_type": "FINAL_ANSWER",
    "thought": "Gemini phản hồi trực tiếp bằng văn bản (không cần gọi công cụ).",
    "output": "Dưới đây là thông tin chi tiết về tiêu chí tuyển dụng của vị trí AI Engineer và kết quả gửi thông báo lịch phỏng vấn cho ứng viên: ### 1. Tiêu chí tuyển dụng vị trí AI Engineer ... (đã tổng hợp đầy đủ JD + xác nhận thư mời phỏng vấn IV-UV2026001-JD-2026-AI01)",
    "latency_ms": 3787.21
  }
]
```

---

## 3. TỔNG KẾT KẾT QUẢ NGHIỆM THU & NỘP BÀI

- [x] Đã điền API Key thật trong `.env` và xác nhận Agent chạy mượt mà trên LLM API thật (Gemini/OpenAI).
- **Tổng số Test Cases đã chạy thành công:** 5 / 5 test cases. *(TC01 → TC05 đều đạt `expected_behavior`; 0 test case nào còn chờ điền câu hỏi)*
- **Số lượt gọi Tool qua MCP Server chính xác:** 6 lượt. *(TC01: 0 · TC02: 1 lượt `job_criteria_query` · TC03: 2 lượt `job_criteria_query` + `send_interview_invitation` · TC04: 2 lượt `job_criteria_query` + `send_interview_invitation` · TC05: 1 lượt `job_criteria_query` trả `NOT_FOUND`)*
- **Kiểm thử chế độ đàm thoại trực tiếp:** [x] Đã chạy `python src/app.py --interactive` thành công trên LLM thật — hỏi *"Hãy tra cứu tiêu chí tuyển dụng của vị trí JD-2026-DA02"* → Agent gọi `job_criteria_query({'job_id': 'JD-2026-DA02'})` và trả về đúng JD của vị trí **Data Analyst**, sau đó thoát phiên bằng `exit`.
- **Kết quả đẩy Repo nộp bài:** [ ] Đã Commit và Push mã nguồn thành công lên GitHub cá nhân.

---

> ✅ **HOÀN TẤT NỘP BÀI:** Sao chép đường link GitHub Repository cá nhân của bạn và dán vào ô nộp bài trên hệ thống LMS VLearn để hoàn tất Bài Lab 3!
