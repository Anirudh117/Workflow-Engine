# 🚀 Minimal Workflow Engine with FastAPI

A lightweight but powerful stateful workflow / graph execution engine built using FastAPI, supporting step-based execution, branching, looping, logging, and tool functions.  
This repository includes a fully working Summarization + Refinement workflow example that demonstrates the engine in action.

---

**🎯 Core Features
- 🧠 Graph-based workflow execution
- 🔄 Stateful pipeline with iterations & conditional routing
- 🪢 Branching and looping support
- 🧰 Tool registry for executable Python functions
- 📄 Execution logs for debugging
- ⚡ REST APIs built with FastAPI
- 🧪 Example summarization workflow included

---

📌 Example Workflow Implemented  
**Summarization + Refinement Pipeline**
| Step | Description |
|------|-------------|
| **1. Split Text** | Breaks long text into smaller chunks |
| **2. Summarize Chunks** | Generates short summaries for each chunk |
| **3. Merge Summaries** | Combines small summaries into a single passage |
| **4. Refine Summary** | Enhances quality and readability |
| **5. Loop until target word limit** | Stops when conditions are met |

---
## 🏗 Project Structure
app/
├── engine/
│ ├── models.py # Data models & run state tracking
│ ├── registry.py # Tool registry logic
│ └── workflow_engine.py # Core workflow execution engine
├── workflows/
│ └── summarization.py # Example summarization workflow
└── main.py # FastAPI routes & initialization


---

## 📡 API Endpoints (FastAPI)
| Method | Endpoint | Description |
|--------|-----------|-------------|
| **POST** | `/graph/create` | Create and register workflow graph |
| **POST** | `/graph/run` | Execute workflow and return final output |
| **GET** | `/graph/state/{run_id}` | Track current workflow execution state |
| **GET** | `/graphs` | List all registered workflows |
| **GET** | `/tools` | List available tool functions |

### 📍 Swagger UI
http://127.0.0.1:8000/docs

---

## 👨‍💻 Author

**M. Anirudhan**  
🔗 GitHub: https://github.com/Anirudh117  
📧 Email: anirudhanm55@gmail.com

> Passionate about building intelligent automation and real-world AI solutions.



---

## 🧪 How to Run Locally
```bash
# Create and activate venv
python -m venv .venv
source .venv/Scripts/activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Start server
uvicorn app.main:app --reload

## 📝 Sample Output
```markdown
## 📝 Sample Output
```json
{
  "final_summary": "AI improves productivity and innovation.",
  "summary_word_count": 14,
  "refinement_done": true,
  "log": [
    {"step": 1, "node": "split_text"},
    {"step": 2, "node": "summarize_chunks"},
    {"step": 3, "node": "merge_summaries"},
    {"step": 4, "node": "refine_summary"}
  ]
}

