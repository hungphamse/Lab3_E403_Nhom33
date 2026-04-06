# Lab 3: Chatbot vs ReAct Agent

## Prerequisites

- **Python 3.10+**
- An **OpenAI API key** (or Gemini API key, or a local GGUF model)

## 1. Setup

### Clone & install dependencies

```bash
cd Lab3_E403_Nhom33
pip install -r requirements.txt
```

### Configure environment variables

Copy the example file and fill in your keys:

```bash
cp .env.example .env
```

Edit `.env` with your preferred provider:

```env
# Required for OpenAI provider
OPENAI_API_KEY=sk-...

# Required for Gemini provider
GEMINI_API_KEY=your_key_here

# Provider selection: openai | google | local
DEFAULT_PROVIDER=openai
DEFAULT_MODEL=gpt-4o
```

## 2. How to Run

### Option A — CLI ReAct Agent demo

Runs a single hardcoded query through the ReAct agent and prints the thought-action-observation trace to the terminal.

```bash
python main.py
```

### Option B — CLI Baseline Chatbot demo

Runs a shoe-purchase query through the plain chatbot (no tools) to demonstrate how the LLM hallucinates prices and stock data.

```bash
python baseline_chatbot.py
```

### Option C — Streamlit Web App (A/B comparison)

Launches a web UI where you can type any query and see the **Baseline Chatbot** and **ReAct Agent** side-by-side.

```bash
streamlit run app.py
```

Then open the URL printed in the terminal (usually `http://localhost:8501`).

## 3. Running Tests

```bash
pytest tests/ -v
```

To test the local Phi-3 model provider specifically:

```bash
python tests/test_local.py
```

## 4. Using a Local Model (CPU, no API key needed)

1. Download the **Phi-3-mini-4k-instruct-q4.gguf** (~2.2 GB) from Hugging Face:
   - [Download link](https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf)

2. Place the file in a `models/` folder at the project root:

   ```
   Lab3_E403_Nhom33/
   └── models/
       └── Phi-3-mini-4k-instruct-q4.gguf
   ```

3. Update `.env`:

   ```env
   DEFAULT_PROVIDER=local
   LOCAL_MODEL_PATH=./models/Phi-3-mini-4k-instruct-q4.gguf
   ```

4. Run any of the commands from **Section 2** above — the local provider will be used automatically.

## 5. Project Structure

```
Lab3_E403_Nhom33/
├── main.py                  # CLI entry point — ReAct Agent demo
├── baseline_chatbot.py      # CLI entry point — Baseline Chatbot demo
├── app.py                   # Streamlit web app (side-by-side comparison)
├── requirements.txt
├── .env.example
├── src/
│   ├── agent/
│   │   └── agent.py         # ReAct Agent implementation
│   ├── core/
│   │   ├── llm_provider.py  # Abstract LLM provider interface
│   │   ├── openai_provider.py
│   │   ├── gemini_provider.py
│   │   └── local_provider.py
│   ├── tools/
│   │   └── shoe_tools.py    # E-commerce tool functions
│   └── telemetry/           # JSON logging for agent traces
├── tests/
│   └── test_local.py
└── report/
```
