import os
from dotenv import load_dotenv
from src.core.openai_provider import OpenAIProvider

def run_shoe_baseline():
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: Please set OPENAI_API_KEY in your .env file.")
        return

    provider = OpenAIProvider(
        model_name=os.getenv("DEFAULT_MODEL", "gpt-4o-mini"),
        api_key=api_key
    )
    
    # Truy vấn mua giày (thách thức chatbot baseline tự suy diễn giá và tồn kho)
    query = (
        "Tôi muốn mua 2 đôi giày Adidas Stan Smith và 1 đôi Nike Air Max 97. "
        "Hãy tính tổng số tiền cho tôi biết, và kiểm tra xem chúng có còn hàng không?"
    )
    
    system_prompt = (
        "Bạn là chuyên gia tư vấn bán giày. Hãy trả lời câu hỏi của người dùng một cách chuyên nghiệp. "
        "Lưu ý: Bạn KHÔNG có quyền truy cập Internet hay cơ sở dữ liệu kho thực tế."
    )
    
    print("=" * 50)
    print("🤖 BASELINE CHATBOT TEST (SHOE CONSULTANT)")
    print("=" * 50)
    print(f"User Query:\n{query}\n")
    print("Generating response... (Watch how the LLM hallucinates prices and stock!)\n")
    
    try:
        response = provider.generate(prompt=query, system_prompt=system_prompt)
        print("--- Response ---")
        print(response["content"])
        print("-" * 16)
        print(f"Latency: {response['latency_ms']} ms | Source: {response['provider']}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    run_shoe_baseline()
