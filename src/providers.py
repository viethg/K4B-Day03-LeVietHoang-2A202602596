"""
🔌 MULTI-PROVIDER LLM ADAPTER (Google Gemini, OpenAI & Offline Mock)
Hỗ trợ Native Tool Calling và chuyển đổi linh hoạt qua biến môi trường LLM_PROVIDER.
"""

import os
import re
import sys
import time
import json
from typing import Dict, Any, List
from dotenv import load_dotenv

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()

# Cấu hình retry khi LLM API bị giới hạn tần suất (HTTP 429 RESOURCE_EXHAUSTED)
# Free tier Gemini giới hạn 5 request/phút/model -> cần chờ và thử lại thay vì rơi ngay về Mock
# (Waterfall Trace nộp bài bắt buộc phải lấy từ LLM API thật).
MAX_RATE_LIMIT_RETRIES = 5
GEMINI_RATE_LIMIT_WAIT_SECONDS = 20

class BaseLLMProvider:
    """Interface cơ sở cho các LLM Provider hỗ trợ Native Tool Calling"""
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        raise NotImplementedError

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        raise NotImplementedError


class MockOfflineProvider(BaseLLMProvider):
    """Offline Mock Provider dùng để chạy thử mà không tốn API Key"""
    def __init__(self):
        self.model_name = "Offline-Mock-Model-2026"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        return (f"[Mock Chatbot Response]: Xin chào! Tôi đã nhận được câu hỏi '{prompt}'. "
                f"(Chế độ Chatbot Baseline Cấp 2 không có Tool tra cứu dữ liệu tuyển dụng thời gian thực).")

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        prompt_lower = prompt.lower()
        # Các Tool đã được Agent gọi trong ngữ cảnh ReAct (đọc từ các dòng "[Action] ..." do app.py nạp vào)
        called_tools = re.findall(r"\[action\]\s*([a-z_]+)\s*\(", prompt_lower)
        # Phần câu hỏi gốc của người dùng (bỏ qua toàn bộ [Action]/[Observation] của các bước trước)
        original_lower = prompt.split("[Action]")[0].lower()

        job_id = self._extract_job_id(prompt)
        candidate_id = self._extract_candidate_id(prompt)
        datetime_str = self._extract_datetime(prompt)

        asks_criteria = any(k in original_lower for k in ("tra cứu", "tiêu chí", "sàng lọc", "job description"))
        wants_interview = any(k in original_lower for k in ("phỏng vấn", "thông báo", "interview"))
        
        # Mô phỏng nhận diện intent gọi Tool theo chủ đề Tuyển dụng & Sàng lọc CV
        # (1) Có mã vị trí + hỏi tiêu chí tuyển dụng -> tra cứu JD trước
        if job_id and asks_criteria and "job_criteria_query" not in called_tools:
            return {
                "type": "tool_call",
                "tool_name": "job_criteria_query",
                "arguments": {"job_id": job_id},
                "thought": f"Người dùng cần tra cứu tiêu chí tuyển dụng của vị trí {job_id}. Tôi sẽ gọi tool job_criteria_query."
            }
        # (2) Có yêu cầu gửi thông báo lịch phỏng vấn -> gọi send_interview_invitation
        #     (bài toán đa bước: Hiring Manager lấy từ Observation của bước (1))
        if job_id and wants_interview and "send_interview_invitation" not in called_tools:
            arguments = {"candidate_id": candidate_id, "job_id": job_id, "datetime_str": datetime_str}
            interviewer = self._extract_field(prompt, "hiring_manager")
            if interviewer:
                arguments["interviewer_name"] = interviewer
            return {
                "type": "tool_call",
                "tool_name": "send_interview_invitation",
                "arguments": arguments,
                "thought": f"Đã có đủ thông tin. Tôi sẽ gọi tool send_interview_invitation cho ứng viên {candidate_id}."
            }
        # (3) Đã có Observation (hoặc câu hỏi kiến thức chung) -> tổng hợp Final Answer
        return {
            "type": "text",
            "content": self._compose_final_answer(prompt),
            "thought": "Đã có đủ dữ liệu, tổng hợp và trả lời trực tiếp."
        }

    @staticmethod
    def _extract_field(context: str, key: str) -> str:
        """Lấy giá trị chuỗi của một key JSON trong ngữ cảnh ReAct."""
        m = re.search(r'"%s":\s*"([^"]*)"' % re.escape(key), context)
        return m.group(1) if m else ""

    @staticmethod
    def _extract_number(context: str, key: str) -> str:
        """Lấy giá trị số của một key JSON trong ngữ cảnh ReAct."""
        m = re.search(r'"%s":\s*([0-9]+)' % re.escape(key), context)
        return m.group(1) if m else ""

    @staticmethod
    def _extract_job_id(context: str) -> str:
        """Lấy mã vị trí tuyển dụng (ví dụ: 'JD-2026-AI01')."""
        m = re.search(r"\bJD-[0-9A-Za-z\-]+", context, flags=re.IGNORECASE)
        return m.group(0) if m else ""

    @staticmethod
    def _extract_candidate_id(context: str) -> str:
        """Lấy mã ứng viên (ví dụ: 'UV2026001')."""
        m = re.search(r"\bUV\d{7}\b", context, flags=re.IGNORECASE)
        return m.group(0) if m else ""

    @staticmethod
    def _extract_datetime(context: str) -> str:
        """Lấy thời gian phỏng vấn (ví dụ: '14:00 15/09/2026')."""
        m = re.search(r"(\d{1,2}:\d{2})\D{1,10}?(\d{1,2}/\d{2}/\d{4})", context)
        return f"{m.group(1)} {m.group(2)}" if m else ""

    def _summarize_criteria(self, context: str) -> str:
        """Tóm tắt tiêu chí tuyển dụng từ Observation (nếu có)."""
        job_title = self._extract_field(context, "job_title")
        if not job_title:
            return ""
        skills_m = re.search(r'"required_skills":\s*\[([^\]]*)\]', context)
        skills = ", ".join(s.strip().strip('"') for s in skills_m.group(1).split(",")) if skills_m else ""
        return (f"Tiêu chí tuyển dụng vị trí {job_title} ({self._extract_field(context, 'job_id')}): "
                f"cấp bậc {self._extract_field(context, 'level')}, tối thiểu {self._extract_number(context, 'min_experience_years')} năm kinh nghiệm; "
                f"kỹ năng: {skills}; {self._extract_field(context, 'education')}; "
                f"{self._extract_field(context, 'gpa_requirement')}; {self._extract_field(context, 'english_requirement')}. "
                f"Hiring Manager: {self._extract_field(context, 'hiring_manager')}.")

    def _compose_final_answer(self, context: str) -> str:
        """Tổng hợp Final Answer từ các Observation trong ngữ cảnh ReAct."""
        # (a) Tool trả về NOT_FOUND -> phản hồi lịch sự, không bịa dữ liệu
        if '"status": "NOT_FOUND"' in context:
            job_id = self._extract_field(context, "job_id") or self._extract_job_id(context)
            return (f"Xin lỗi, tôi không tìm thấy vị trí tuyển dụng nào có mã '{job_id}' trong hệ thống. "
                    f"Bạn vui lòng kiểm tra lại mã vị trí (định dạng mẫu: 'JD-2026-AI01') và gửi lại yêu cầu.")
        criteria = self._summarize_criteria(context)
        # (b) Đã gửi thông báo phỏng vấn -> xác nhận theo đúng dữ liệu Tool trả về
        invitation_id = self._extract_field(context, "invitation_id")
        if invitation_id:
            confirmation = (f"Đã gửi thông báo lịch phỏng vấn (mã {invitation_id}) tới ứng viên "
                            f"{self._extract_field(context, 'candidate_id')} cho vị trí {self._extract_field(context, 'job_title')} "
                            f"({self._extract_field(context, 'job_id')}) với {self._extract_field(context, 'interviewer')} "
                            f"vào lúc {self._extract_field(context, 'datetime')}.")
            return f"{criteria}\n\n{confirmation}" if criteria else confirmation
        # (c) Chỉ tra cứu tiêu chí tuyển dụng
        if criteria:
            return criteria
        # (d) Câu hỏi kiến thức chung -> trả lời trực tiếp, không gọi Tool
        return ("Quy trình tuyển dụng & sàng lọc CV tại VinUni gồm 4 bước: (1) Sàng lọc CV theo tiêu chí của vị trí; "
                "(2) Phỏng vấn sơ loại; (3) Phỏng vấn chuyên môn với Hiring Manager; (4) Thương lượng & gửi Đề nghị làm việc. "
                "Bạn có thể nhờ tôi tra cứu tiêu chí một vị trí cụ thể hoặc gửi thông báo lịch phỏng vấn cho ứng viên.")


class GeminiProvider(BaseLLMProvider):
    """Google Gemini Provider (Native Tool Calling với Google GenAI SDK)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gemini-2.5-flash"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            return "[Gemini Error]: Chưa cấu hình GEMINI_API_KEY trong file .env! Đang sử dụng chế độ Mock."
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            contents = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            response = client.models.generate_content(model=self.model_name, contents=contents)
            return response.text
        except Exception as e:
            return f"[Gemini Exception]: {str(e)}"

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            print("ℹ️ [Gemini Provider]: Chưa tìm thấy GEMINI_API_KEY hợp lệ. Tự động chuyển sang Mock Offline.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)
        
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)
            
            # Chuẩn hóa function declarations cho Gemini SDK
            function_declarations = []
            for tool in tools_schema:
                # Bỏ qua các tool schema chưa được định nghĩa hoàn chỉnh
                if not tool.get("name") or not tool.get("parameters"):
                    continue
                function_declarations.append({
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("parameters", {})
                })

            config = types.GenerateContentConfig(
                system_instruction=system_prompt if system_prompt else None,
                tools=[{"function_declarations": function_declarations}] if function_declarations else None,
                temperature=0.2
            )

            # Gọi API có retry khi bị giới hạn tần suất (429) để giữ trace từ LLM thật
            response = None
            for attempt in range(MAX_RATE_LIMIT_RETRIES + 1):
                try:
                    response = client.models.generate_content(
                        model=self.model_name,
                        contents=prompt,
                        config=config
                    )
                    break
                except Exception as api_error:
                    is_rate_limited = ("429" in str(api_error)) or ("RESOURCE_EXHAUSTED" in str(api_error))
                    if not is_rate_limited or attempt >= MAX_RATE_LIMIT_RETRIES:
                        raise
                    print(f"⏳ [Gemini Rate Limit]: Bị giới hạn tần suất (429). Chờ {GEMINI_RATE_LIMIT_WAIT_SECONDS}s rồi thử lại (lần {attempt + 1}/{MAX_RATE_LIMIT_RETRIES})...")
                    time.sleep(GEMINI_RATE_LIMIT_WAIT_SECONDS)

            # Kiểm tra xem Gemini có trả về Tool Call không
            if response.function_calls:
                call = response.function_calls[0]
                args = dict(call.args) if hasattr(call, 'args') and call.args else {}
                return {
                    "type": "tool_call",
                    "tool_name": call.name,
                    "arguments": args,
                    "thought": f"Gemini quyết định gọi công cụ '{call.name}' với tham số: {json.dumps(args, ensure_ascii=False)}"
                }
            else:
                return {
                    "type": "text",
                    "content": response.text or "",
                    "thought": "Gemini phản hồi trực tiếp bằng văn bản (không cần gọi công cụ)."
                }

        except Exception as e:
            print(f"⚠️ [Gemini API Warning]: Không thể kết nối live API ({str(e)}). Tự động fallback về Mock.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI Provider (Native Tool Calling với OpenAI SDK)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gpt-4o-mini"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            return "[OpenAI Error]: Chưa cấu hình OPENAI_API_KEY trong file .env! Đang sử dụng chế độ Mock."
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            response = client.chat.completions.create(model=self.model_name, messages=messages)
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"[OpenAI Exception]: {str(e)}"

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            print("ℹ️ [OpenAI Provider]: Chưa tìm thấy OPENAI_API_KEY hợp lệ. Tự động chuyển sang Mock Offline.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)

            tools = []
            for tool in tools_schema:
                if not tool.get("name"):
                    continue
                tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool.get("parameters", {})
                    }
                })

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None
            )

            msg = response.choices[0].message
            if msg.tool_calls:
                call = msg.tool_calls[0]
                args = json.loads(call.function.arguments) if call.function.arguments else {}
                return {
                    "type": "tool_call",
                    "tool_name": call.function.name,
                    "arguments": args,
                    "thought": f"OpenAI quyết định gọi công cụ '{call.function.name}' với tham số: {json.dumps(args, ensure_ascii=False)}"
                }
            else:
                return {
                    "type": "text",
                    "content": msg.content or "",
                    "thought": "OpenAI phản hồi trực tiếp bằng văn bản (không cần gọi công cụ)."
                }
        except Exception as e:
            print(f"⚠️ [OpenAI API Warning]: Không thể kết nối live API ({str(e)}). Tự động fallback về Mock.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)


def get_llm_provider() -> BaseLLMProvider:
    """Factory function khởi tạo Provider theo LLM_PROVIDER env variable"""
    provider_type = os.getenv("LLM_PROVIDER", "gemini").lower()
    
    if provider_type == "gemini":
        key = os.getenv("GEMINI_API_KEY")
        if key and key != "your_gemini_api_key_here":
            return GeminiProvider()
        else:
            return MockOfflineProvider()
    elif provider_type == "openai":
        key = os.getenv("OPENAI_API_KEY")
        if key and key != "your_openai_api_key_here":
            return OpenAIProvider()
        else:
            return MockOfflineProvider()
    elif provider_type == "mock":
        return MockOfflineProvider()
    else:
        return MockOfflineProvider()
