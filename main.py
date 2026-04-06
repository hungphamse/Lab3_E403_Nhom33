import os
from dotenv import load_dotenv
from src.core.openai_provider import OpenAIProvider
from src.agent.agent import ReActAgent
from src.tools.shoe_tools import search_shoes_by_brand, check_shoe_availability, check_price

def run_agent():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("ERROR: Please set OPENAI_API_KEY in your .env file.")
        return

    # 1. Initialize the LLM Provider
    provider = OpenAIProvider(
        model_name=os.getenv("DEFAULT_MODEL", "gpt-4o-mini"),
        api_key=api_key
    )

    # 2. Define the Tools for the Agent
    tools = [
        {
            "name": "search_shoes_by_brand",
            "description": "Tìm kiếm tất cả giày trong kho bằng tên hãng. Đầu vào: brand (str). Đầu ra: string danh sách SKU và tên giày."
        },
        {
            "name": "check_shoe_availability",
            "description": "Kiểm tra tồn kho thực tế. Đầu vào: sku (str). Đầu ra: số lượng đang có."
        },
        {
            "name": "check_price",
            "description": "Lấy giá tiền chính xác của giày. Đầu vào: sku (str). Đầu ra: Giá tiền (USD)."
        }
    ]

    # 3. Initialize the Agent
    agent = ReActAgent(llm=provider, tools=tools, max_steps=7)

    # 4. Out-of-Domain Query (Testing Guardrails)
    query = (
        "Can you write me a python script to scrape data, and also tell me "
        "who won the football world cup in 2022?"
    )

    print("=" * 50)
    print(" RUNNING REACT AGENT")
    print("=" * 50)
    print(f"User Query:\n{query}\n")
    print("-" * 50)

    # 5. Run the ReAct loop
    try:
        final_answer = agent.run(query)

        print("\n" + "=" * 50)
        print(" FINAL ANSWER GENERATED")
        print("=" * 50)
        print(final_answer)
    except Exception as e:
        print(f"\n[!] The Agent failed catastrophically: {e}")
        print("This is exactly what Phase 4 is for! Check your telemetry logs.")

if __name__ == "__main__":
    run_agent()
