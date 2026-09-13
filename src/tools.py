"""
🛠️ TOOL DEFINITIONS & EXECUTION BACKEND
Mã nguồn chứa danh sách Tool Schemas (JSON Schema) và Execution Layer phục vụ cho MCP Server.

📌 Chủ đề bài toán: Trợ lý Tuyển dụng & Sàng lọc CV
   (1) job_criteria_query        - Tra cứu tiêu chí tuyển dụng (JD) của một vị trí.
   (2) send_interview_invitation - Gửi thông báo lịch phỏng vấn cho ứng viên.
"""

import json
from typing import Dict, Any, Optional

# ==============================================================================
# 1. KHAI BÁO TOOL SCHEMAS CHUẨN NATIVE JSON SCHEMA (TASK 1.2)
# ==============================================================================

TOOLS_SCHEMA = [
    # Tool 1 (giữ nguyên cấu trúc mẫu đã cho, chỉ đổi domain sang Tuyển dụng):
    # Công cụ TRA CỨU dữ liệu tuyển dụng -> trả về SUCCESS/NOT_FOUND
    {
        "name": "job_criteria_query",
        "description": "Tra cứu tiêu chí tuyển dụng (Job Description) của một vị trí tại VinUni bằng mã vị trí.",
        "parameters": {
            "type": "object",
            "properties": {
                "job_id": {
                    "type": "string",
                    "description": "Mã vị trí tuyển dụng cần tra cứu (ví dụ: 'JD-2026-AI01')"
                }
            },
            "required": ["job_id"]
        }
    },
    
    # --------------------------------------------------------------------------
    # [ĐÃ HOÀN THIỆN - TASK 1.2] TOOL SCHEMA CHO 'send_interview_invitation'
    # 🎯 YÊU CẦU THIẾT KẾ SCHEMA (JSON SCHEMA STANDARD):
    # 1. Tool dùng để gửi thông báo lịch phỏng vấn tới ứng viên đã qua vòng sàng lọc CV.
    # 2. Các tham số (properties) để LLM trích xuất:
    #    - candidate_id (string): Mã ứng viên cần gửi thông báo (ví dụ: 'UV2026001')
    #    - job_id (string): Mã vị trí tuyển dụng ứng viên đã ứng tuyển (ví dụ: 'JD-2026-AI01')
    #    - datetime_str (string): Thời gian phỏng vấn (ví dụ: '14:00 15/09/2026')
    #    - interviewer_name (string): Tên người phỏng vấn / Hiring Manager (lấy từ kết quả
    #      của 'job_criteria_query'; nếu bỏ trống Tool sẽ tự tra cứu theo job_id)
    # 3. Danh sách các trường bắt buộc (required): candidate_id, job_id, datetime_str
    # --------------------------------------------------------------------------
    {
        "name": "send_interview_invitation",
        "description": "Gửi thông báo lịch phỏng vấn cho ứng viên ứng tuyển một vị trí tuyển dụng tại VinUni.",
        "parameters": {
            "type": "object",
            "properties": {
                "candidate_id": {
                    "type": "string",
                    "description": "Mã ứng viên cần gửi thông báo lịch phỏng vấn (ví dụ: 'UV2026001')"
                },
                "job_id": {
                    "type": "string",
                    "description": "Mã vị trí tuyển dụng mà ứng viên ứng tuyển (ví dụ: 'JD-2026-AI01')"
                },
                "datetime_str": {
                    "type": "string",
                    "description": "Thời gian phỏng vấn (ví dụ: '14:00 15/09/2026')"
                },
                "interviewer_name": {
                    "type": "string",
                    "description": "Tên người phỏng vấn / Hiring Manager phụ trách vị trí (nên lấy từ kết quả 'job_criteria_query')"
                }
            },
            "required": ["candidate_id", "job_id", "datetime_str"]
        }
    }
]

# ==============================================================================
# 2. MÔ PHỎNG DỮ LIỆU & HÀM THỰC THI TOOL (EXECUTION LAYER)
# ==============================================================================

MOCK_DATABASE = {
    "JD-2026-AI01": {
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
    },
    "JD-2026-DA02": {
        "job_title": "Data Analyst",
        "department": "Khối Công nghệ & Dữ liệu",
        "level": "Fresher/Junior",
        "required_skills": ["SQL", "Power BI/Tableau", "Excel nâng cao", "Statistics"],
        "min_experience_years": 1,
        "education": "Tốt nghiệp Đại học ngành Kinh tế / Khoa học dữ liệu",
        "gpa_requirement": "GPA >= 2.8/4.0",
        "english_requirement": "IELTS 6.0+ hoặc tương đương",
        "hiring_manager": "ThS. Trần Thị B",
        "status": "Đang mở"
    }
}


def execute_job_criteria_query(job_id: str) -> str:
    """Thực thi tra cứu tiêu chí tuyển dụng theo mã vị trí (Job ID)"""
    job = MOCK_DATABASE.get(job_id.strip().upper())
    if job:
        return json.dumps({
            "status": "SUCCESS",
            "job_id": job_id,
            "data": job
        }, ensure_ascii=False)
    else:
        return json.dumps({
            "status": "NOT_FOUND",
            "message": f"Không tìm thấy vị trí tuyển dụng có mã '{job_id}'"
        }, ensure_ascii=False)


def execute_send_interview_invitation(candidate_id: str, job_id: str, datetime_str: str, interviewer_name: Optional[str] = None) -> str:
    """Thực thi gửi thông báo lịch phỏng vấn tới ứng viên"""
    job = MOCK_DATABASE.get(job_id.strip().upper(), {})
    interviewer = interviewer_name or job.get("hiring_manager") or "Hội đồng Tuyển dụng VinUni"
    job_title = job.get("job_title", job_id)

    return json.dumps({
        "status": "SUCCESS",
        "invitation_id": f"IV-{candidate_id}-{job_id}",
        "candidate_id": candidate_id,
        "job_id": job_id,
        "job_title": job_title,
        "datetime": datetime_str,
        "interviewer": interviewer,
        "message": f"Đã gửi thông báo lịch phỏng vấn tới ứng viên {candidate_id} cho vị trí {job_title} ({job_id}) với {interviewer} vào lúc {datetime_str}."
    }, ensure_ascii=False)


# Router gọi tool thực tế
TOOL_ROUTER = {
    "job_criteria_query": execute_job_criteria_query,
    "send_interview_invitation": execute_send_interview_invitation
}

def dispatch_tool_call(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Hàm trung chuyển thực thi tool"""
    if tool_name in TOOL_ROUTER:
        try:
            return TOOL_ROUTER[tool_name](**arguments)
        except Exception as e:
            return json.dumps({"status": "EXECUTION_ERROR", "error": str(e)}, ensure_ascii=False)
    return json.dumps({"status": "UNKNOWN_TOOL", "error": f"Tool '{tool_name}' không tồn tại!"}, ensure_ascii=False)
