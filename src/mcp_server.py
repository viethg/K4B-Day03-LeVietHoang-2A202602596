"""
🔌 MODEL CONTEXT PROTOCOL (MCP) SERVER MODULE
Mô phỏng kiến trúc MCP Server (Client-Server Architecture) cung cấp công cụ chuẩn hóa.
"""

import json
import sys
from typing import Dict, Any, List
from tools import TOOLS_SCHEMA, dispatch_tool_call

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

class MCPRecruitmentServer:
    """
    Giả lập MCP Server (chủ đề Tuyển dụng & Sàng lọc CV) tuân thủ chuẩn giao thức Model Context Protocol
    """
    def __init__(self, server_name: str = "vinuni-recruitment-mcp-server"):
        self.server_name = server_name
        self.version = "2026.1.0"
        
    def list_tools(self) -> List[Dict[str, Any]]:
        """Trả về danh sách các Tools chuẩn giao thức MCP"""
        return TOOLS_SCHEMA
        
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        [ĐÃ HOÀN THIỆN - TASK 2.1] HÀM THỰC THI TOOL TRÊN MCP SERVER
        Thực thi request gọi Tool theo chuẩn MCP JSON-RPC 2.0

        🎯 THUẬT TOÁN:
        1. Gọi hàm dispatch_tool_call(tool_name, arguments) để lấy chuỗi JSON kết quả từ Tool Router.
        2. Chuyển đổi chuỗi JSON kết quả thành Python Dictionary (dùng json.loads).
        3. Đóng gói phản hồi và trả về Dict theo đúng chuẩn giao thức MCP JSON-RPC 2.0:
           - Các trường bắt buộc: "jsonrpc": "2.0", "server": self.server_name, "tool": tool_name, "result": content
        """
        # Bước 1: Chuyển yêu cầu xuống Tool Router (Execution Layer trong src/tools.py)
        raw_json = dispatch_tool_call(tool_name, arguments)

        # Bước 2: Giải mã chuỗi JSON -> Python Dictionary để đóng gói vào trường "result"
        try:
            content = json.loads(raw_json)
        except (json.JSONDecodeError, TypeError):
            content = {
                "status": "EXECUTION_ERROR",
                "message": f"Tool Router trả về dữ liệu không phải JSON hợp lệ: {raw_json}"
            }

        # Bước 3: Đóng gói phản hồi chuẩn MCP JSON-RPC 2.0
        return {
            "jsonrpc": "2.0",
            "server": self.server_name,
            "tool": tool_name,
            "result": content
        }


if __name__ == "__main__":
    print("==========================================================")
    print("🔌 KIỂM THỬ ĐỘC LẬP MCP SERVER (Recruitment MCP Server)")
    print("==========================================================")
    
    server = MCPRecruitmentServer()
    tools = server.list_tools()
    print(f"✅ [MCP SERVER] Đã khởi tạo thành công {server.server_name} (Version: {server.version})")
    print(f"📦 Số lượng Tools công bố qua MCP: {len(tools)}")
    
    # Kiểm tra trạng thái TODO 1.2 (Tool Schema)
    invite_tool = next((t for t in tools if t.get("name") == "send_interview_invitation"), None)
    if invite_tool and not invite_tool.get("parameters", {}).get("properties"):
        print("⏳ [TODO 1.2]: Tool 'send_interview_invitation' chưa được định nghĩa properties trong 'src/tools.py'.")
    else:
        print("✅ [TODO 1.2]: Tool 'send_interview_invitation' đã có schema đầy đủ.")

    # Kiểm tra trạng thái TODO 2.1 (call_tool)
    test_result = server.call_tool("job_criteria_query", {"job_id": "JD-2026-AI01"})
    if not test_result:
        print("⏳ [TODO 2.1]: Hàm call_tool() đang trả về rỗng. Học viên hãy hoàn thiện TODO 2.1 trong 'src/mcp_server.py'!")
    else:
        print(f"✅ [TODO 2.1]: Test dispatch tool 'job_criteria_query' thành công:")
        print(f"   Phản hồi JSON-RPC: {json.dumps(test_result, ensure_ascii=False)}")
