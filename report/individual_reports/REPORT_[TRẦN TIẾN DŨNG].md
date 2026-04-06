# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Trần Tiến Dũng
- **Student ID**: 2A202600314
- **Date**: 06/04/2026

---

## I. Technical Contribution (15 Points)

*Describe your specific contribution to the codebase (e.g., implemented a specific tool, fixed the parser, etc.).*

- **Modules Implementated**: `src/tools/shoe_tools.py`, `src/agent/agent.py`, `app.py`
- **Code Highlights**:
```python
def check_shoe_availability(sku: str) -> str:
    """
    Checks the inventory stock level for a specific shoe.
    Input: sku (str) - The unique product ID (e.g., 'NK-8821').
    Returns: (str) The available quantity, or out of dataset message if not found.
    """
    oku_upper = sku.upper()
    if oku_upper not in SHOE_DATABASE:
        return OUT_OF_DATASET_MSG
    stock = SHOE_DATABASE[oku_upper]["stock"]
    return f"{stock} units available." if stock > 0 else "0 units available (Out of stock)."
```
- **Documentation**: Em đã xây tạo bộ mock data gồm các hãng Nike, Adidas, Puma; thêm phần xử lý ngoài dataset để kết nối logic với OpenAI API. Và em thiết lập system prompt cho ReAct loop trong `agent.py` chặn hallucination dựa trên Tool và bắt buộc trả lời câu từ chối chuẩn khi bị người dùng hỏi những câu out of domain.

---

## II. Debugging Case Study (10 Points)

*Analyze a specific failure event you encountered during the lab using the logging system.*

- **Problem Description**: ReAct Agent bị lỗi trả về kết quả mà bỏ qua tool `check_shoe_availability` khi tính tổng giá tiền hoặc gặp lỗi reach max_steps limit khi câu hỏi bắt tính toán quá nhiều mã giày cùng lúc.
- **Log Source**: `logs/2026-04-06.log` -> `{"timestamp": "...", "event": "AGENT_ESCALATION", "data": {"steps": 5, "status": "failed_max_steps"}}`
- **Diagnosis**: Agent đã nhận diện khi tìm total price chỉ cần tham số giảm giá và phí vận chuyển, do đó tự động bypass bước kiểm tra tồn kho. Với những lệnh yêu cầu nhiều hơn, số vòng lặp max_steps=5 không đủ dẫn đến Agent bị ngắt trước khi tìm ra đáp án.
- **Solution**: Em đã viết System Prompt quy định rõ Ràng buộc (CRITICAL RULES): "1. Không bao giờ tự phỏng đoán mức tồn kho mà không gọi Tools chính xác." và tích hợp thanh trượt trên UI để tùy chỉnh vòng lặp lên max_steps=7.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

*Reflect on the reasoning capability difference.*

1.  **Reasoning**: Nhờ khối lệnh `Thought`, Agent được trao dải thời gian nhận thức nó đang thiếu dữ liệu gì và thay vì bịa ra kết quả như Chatbot truyền thống, nó tự lên kế hoạch "Tôi cần tra tên hãng, sau đó check tồn kho". 
2.  **Reliability**: Trong các câu hỏi đơn giản không cần realtime data, Chatbot sẽ nhanh và rẻ hơn. ReAct Agent có latency cao hơn vì phải tốn tài nguyên "Suy nghĩ -> Gọi Tool" cho những việc cơ bản. Nhưng thực tế khi test em thấy ReAct có latency thấp hơn và token thấp hơn
3.  **Observation**: Kết quả `Observation` trả về từ Tool giúp giảm hallucination. Khi Tool báo ngoại lệ `OUT_OF_DATASET`, Agent nhận biết và chuyển sang việc tận dụng quyền nhờ OpenAI.

---

## IV. Future Improvements (5 Points)

*How would you scale this for a production-level AI agent system?*

- **Scalability**: Áp dụng Function Calling tích hợp thẳng của OpenAI thay cho việc phải bóc tách thủ công bằng thuật toán Regex ở string text để đẩy nhanh luồng đọc Action.
- **Safety**: Xây dựng Guardian Agent cho security đứng trước Proxy để lọc câu hỏi vô nghĩa hoặc tấn công prompt injection trước khi truy vấn tốn Token vào Agent Tư vấn Giày.
- **Performance**: Khi Database Tool mở rộng hàng ngàn hàm API khác nhau, ta sẽ cần cài đặt phương pháp RAG (Vector Search DB) cho Tool Descriptions để System Prompt không bị nặng, Agent chỉ nạp đúng 3-5 Tool có định nghĩa sát nghĩa nhất với yêu cầu khách hàng.

---

> [!NOTE]
> Submit this report by renaming it to `REPORT_[YOUR_NAME].md` and placing it in this folder.
