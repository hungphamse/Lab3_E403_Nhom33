import os
from dotenv import load_dotenv
from src.core.openai_provider import OpenAIProvider
from src.agent.agent import ReActAgent
from src.tools.ecommerce_tools import check_stock, get_discount, calc_shipping

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

    # 2. Define the Tools for the Agent (Notice how critical the descriptions are!)
    tools = [
        {
            "name": "check_stock",
            "description": "Queries inventory database. Input: item_sku (str) - The exact 8-character alphanumeric product ID. Returns: (int) Available quantity in units. Returns 0 if out of stock."
        },
        {
            "name": "get_discount",
            "description": "Calculates new total after discount application. Input: promo_code (str) and cart_total (float) separated by a comma. Example: SAVE20, 2000.0. Returns: (float) Adjusted cart total."
        },
        {
            "name": "calc_shipping",
            "description": "Calculates shipping rate. Input: weight_kg (float) and destination_zip (str) separated by a comma. Example: 1.5, 90210. Returns: (float) Shipping cost in USD."
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
