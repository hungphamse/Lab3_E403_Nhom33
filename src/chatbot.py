from src.agent.agent import ReActAgent;
from src.core.openai_provider import OpenAIProvider;
import dotenv

from src.tools import get_weather;

if __name__ == "__main__":
    apiKey = dotenv.get_key(".env", "OPENAI_API_KEY")
    agent = ReActAgent(llm=OpenAIProvider(api_key=apiKey), tools=[{
        "name": "get_weather",
        "callable": get_weather,
        "description": """
        Get the current weather for a location. Args: 
            location (str): the location for which to get weather information, 
            unit (str, optional): the unit for temperature (celsius, fahrenheit, kelvin). Defaults to celsius.
        """
    }])
    while True:
        user_input = input("User: ")
        if user_input.lower() in ("exit", "quit"):
            print("Exiting chatbot. Goodbye!")
            break
        response = agent.run(user_input)
        print(f"Agent: {response}\n\n")