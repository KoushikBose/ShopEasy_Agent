# ShopEasy Returns Agent

An AI agent that handles returns and exchanges for an online store. It reads orders from a database, searches a policy handbook (RAG), decides, and books returns. Guardrails in code and a staff approval step keep it safe.

**Agent = LLM + Tools + Memory + Loop**

> Diagrams below use Mermaid. In VS Code, install the extension **Markdown Preview Mermaid Support** (`bierner.markdown-mermaid`), then press `Ctrl+Shift+V` to preview this file.

## 1. System overview

```mermaid
flowchart LR
    subgraph UI["User interfaces"]
        CHAT["chat.py<br/>terminal chat"]
        APP["app.py<br/>Streamlit chat + staff sidebar"]
        EVALS["evals.py<br/>golden dataset tests"]
    end

    AGENT["agent.py<br/>LLM (Groq gpt-oss-120b)<br/>+ system prompt (prompts.py)<br/>+ InMemorySaver memory<br/>+ ToolCallLimit = 10"]

    subgraph TOOLS["tools.py"]
        T1["get_orders"]
        T2["search_knowledge"]
        T3["create_return"]
        T4["create_exchange"]
        GR{{"Guardrails"}}
    end

    DB[("database.py<br/>SQLite shopeasy.db")]
    RAG["retrieval.py<br/>Qdrant in-memory + fastembed"]
    KB[/"knowledge/<br/>handbook.txt, catalog.txt"/]

    CHAT --> AGENT
    APP --> AGENT
    EVALS --> AGENT
    AGENT <--> T1 & T2 & T3 & T4
    T1 --> DB
    T3 & T4 --> GR --> DB
    T2 --> RAG
    KB -. indexed at startup .-> RAG
    APP -- "approve / reject" --> DB
```

## 2. One message through the agent (the loop)

```mermaid
flowchart TD
    A([Customer sends a message]) --> B["Login context attached<br/>customer_id, thread_id for memory"]
    B --> C["LLM reads: system prompt + memory + message"]
    C --> D{"Needs a tool?"}
    D -- No --> H["LLM writes final reply"]
    D -- Yes --> E["LLM asks for a tool<br/>get_orders / search_knowledge /<br/>create_return / create_exchange"]
    E --> F{"Tool calls so far > 10?"}
    F -- Yes --> H
    F -- No --> G["Agent runs the tool<br/>result goes back to the LLM"]
    G --> C
    H --> I[("Saved to memory")]
    I --> J([Customer sees the reply])
```

## 3. Guardrails: create_return / create_exchange

The LLM decides from the handbook. These checks run in code, so the LLM cannot get around them.

```mermaid
flowchart TD
    S(["create_return(order_id)<br/>create_exchange(order_id, new_size)"]) --> G1{"1. Is it this<br/>customer's order?"}
    G1 -- No --> R1["Refused"]
    G1 -- Yes --> G2{"2. Already booked<br/>return or exchange?"}
    G2 -- Yes --> R2["Refused"]
    G2 -- No --> G3{"3. Electronics?"}
    G3 -- Yes --> R3["Refused (handbook s.13)"]
    G3 -- No --> K{"Which tool?"}

    K -- create_return --> P{"Price > Rs 10,000?"}
    P -- Yes --> W[("Booked: waiting_for_staff")]
    P -- No --> AP[("Booked: approved<br/>pickup in 2 days")]

    K -- create_exchange --> SZ{"Item has a size?"}
    SZ -- No --> R4["Refused"]
    SZ -- Yes --> ST{"New size in stock?"}
    ST -- No --> R5["Out of stock<br/>offer return instead"]
    ST -- Yes --> EX[("Take from stock<br/>Booked: approved")]

    W --> STAFF["Staff sidebar in app.py<br/>or 'staff' command in chat.py"]
    STAFF --> D{"Staff decision"}
    D --> APPR[("approved")]
    D --> REJ[("rejected")]
```

## 4. Retrieval (RAG) in retrieval.py

```mermaid
flowchart TD
    subgraph INDEX["Indexing (once, at startup)"]
        F[/"handbook.txt<br/>catalog.txt"/] --> SP["Split into passages<br/>(one per paragraph)"]
        SP --> V1["Dense vector<br/>bge-small-en-v1.5 (meaning)"]
        SP --> V2["Sparse vector<br/>BM25 (exact words)"]
        V1 & V2 --> Q[("Qdrant in-memory<br/>tagged by source")]
    end

    subgraph SEARCH["Searching (each search_knowledge call)"]
        QU(["query + source"]) --> H1["Meaning search, top 10"]
        QU --> H2["Word search, top 10"]
        H1 & H2 --> RRF["RRF merge, top 10"]
        RRF --> RR["Cross-encoder rerank<br/>ms-marco-MiniLM"]
        RR --> OUT(["Best 3 passages to the LLM"])
    end

    Q -.-> H1
    Q -.-> H2
```

## 5. Run order

```mermaid
flowchart LR
    S1["setup.bat / setup.sh<br/>install + create .env"] --> S2["Add GROQ_API_KEY to .env"]
    S2 --> S3["python database.py<br/>create and seed the DB"]
    S3 --> S4{"Choose"}
    S4 --> C1["python chat.py"]
    S4 --> C2["streamlit run app.py"]
    S4 --> C3["python evals.py"]
```

## Files

| File | Role |
|---|---|
| `database.py` | Customers, orders, returns, stock (SQLite) |
| `retrieval.py` | Hybrid search + rerank over handbook and catalog |
| `tools.py` | The 4 tools and the guardrails |
| `prompts.py` | System prompt versions |
| `agent.py` | Builds the agent: LLM + tools + memory + loop limit |
| `chat.py` | Terminal chat |
| `app.py` | Streamlit chat with staff approvals |
| `evals.py` | Runs the agent on `golden_dataset.csv` |
| `flow.html`, `architecture.html` | Interactive versions of these diagrams (open in a browser) |

See [LAB.md](LAB.md) for the step-by-step lab.
