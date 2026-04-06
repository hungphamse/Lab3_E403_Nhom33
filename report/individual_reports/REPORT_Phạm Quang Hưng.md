# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Phạm Quang Hưng
- **Student ID**: 2A20260266
- **Date**: 2026-04-06

---

## I. Technical Contribution (15 Points)

Adding group report, pinpoint the hallucinate edge case, implement agent.py

- **Modules Implementated**: src/agent/agent.py
- **Code Highlights**: 
```python
    func = tool.get('func') or tool.get('callable') or tool.get('run') or tool.get('execute')
    if callable(func):
        try:
            parsed_args = ast.literal_eval(args) if args else ()
            # Try calling with the raw args string first
            return str(func(*parsed_args))
        except TypeError:
            try:
                # Try calling without args
                return str(func())
            except Exception as e:
                return f"Error executing {tool_name}: {e}"
        except Exception as e:
            return f"Error executing {tool_name}: {e}"
```
- **Documentation**: Implement agent.py provide tools for baseline agent

## II. Debugging Case Study (10 Points)

The CLI displayed repeated ACTION_CALL and then en

- **Problem Description**: Agent caught in an infinite loop with `Action: search_shoes_by_brand(None)`
- **Log Source**: `logs/2026-04-06.log`
- **Diagnosis**: Due to the way the function does not resolve the args (which is string). The args were not parse properly.
- **Solution**: Adding a one-line parse function from string to proper args list

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1.  **Reasoning**: The Though block provide precised tool callings compared to Chatbot
2.  **Reliability**: Chatbot use lesser token for the same result
3.  **Observation**: The observation help the model to choose proper next step (either responding or using the result for next tool calling)

---

## IV. Future Improvements (5 Points)

- **Scalability**: Use more dedicated AI type for ReAct
- **Safety**: Implement a "supervise" agent + "prompt injection finder" agent
- **Performance**: Adding RAG for documentation retrieving
