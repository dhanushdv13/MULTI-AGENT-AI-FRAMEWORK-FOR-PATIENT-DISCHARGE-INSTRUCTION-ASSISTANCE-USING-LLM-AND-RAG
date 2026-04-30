# Multi-Agent System -- Complete End-to-End Deep Dive

## Table of Contents
1. What is a Multi-Agent System?
2. Architecture Overview -- How Agents Connect
3. The Entry Point -- How a User Question Reaches the Agents
4. The Orchestrator -- The Traffic Controller
5. The BaseAgent -- Shared DNA of All Agents
6. Agent 1: Discharge Summary Agent
7. Agent 2: Diet and Nutrition Agent
8. Agent 3: Bill Validator Agent (Placeholder)
9. Agent 4: Medicine Price Agent (Placeholder) + Pharmacy Scraper
10. The Vector Store -- How Agents Search Documents
11. The Embedding Engine -- Converting Text to Numbers
12. End-to-End Flow Walkthrough (Step by Step)
13. Summary Table of All Components

---

## 1. What is a Multi-Agent System?

Imagine you go to a hospital reception desk with a question. The receptionist (the Orchestrator) listens to you and decides: "This is a diet question, let me send you to the nutritionist." Or: "This is about your bill, let me send you to the billing department."

That is exactly what this project does with AI. Instead of one giant AI that tries to do everything, the system has multiple specialized "agents," each trained (via prompts) to handle one type of question. A central manager called the Orchestrator reads the user's question, figures out which agent is best suited, and routes it there.

The key agents in this system are:
- Discharge Summary Agent -- Answers questions about medical reports
- Diet and Nutrition Agent -- Creates meal plans and dietary advice
- Bill Validator Agent -- (Placeholder) Will validate hospital bills
- Medicine Price Agent -- (Placeholder) Will compare medicine prices online

---

## 2. Architecture Overview -- How Agents Connect

Here is the complete chain from user question to AI answer:

```
User types: "What medicines were prescribed?"
       |
       v
[Frontend] sends POST /chat/{vector_id}
       |
       v
[chat.py] receives message, creates Orchestrator
       |
       v
[Orchestrator] asks Gemini LLM: "Which agent should handle this?"
       |
       v
LLM responds: "Discharge Summary Agent"
       |
       v
[Orchestrator] calls DischargeSummaryAgent.process_async(query)
       |
       v
[DischargeSummaryAgent] calls search_discharge_async(query)
       |
       v
[BaseAgent] calls search_document_async(vector_id, query)
       |
       v
[DocumentVectorStore] converts query to embedding via embeddings.py
       |
       v
[FAISS Index] finds the 5 most similar text chunks
       |
       v
[DischargeSummaryAgent] formats chunks + query into a prompt
       |
       v
[Google Gemini LLM] generates a human-readable answer
       |
       v
[chat.py] returns {agent: "Discharge Summary Agent", response: "..."}
       |
       v
[Frontend] displays the answer in the chat interface
```

---

## 3. The Entry Point -- chat.py

File: backend/app/routes/chat.py

When the user sends a message in the chat interface, the frontend sends a POST request to /chat/{vector_id}. The vector_id identifies which uploaded document the user is asking about.

Here is what happens step by step:

Step 1: The endpoint receives the message and the vector_id from the URL.

Step 2: It checks if this vector_id belongs to the logged-in user by querying MongoDB. This prevents users from accessing other people's documents.

Step 3: It creates an Orchestrator object, passing in the vector_id. This is the AI manager.

Step 4: It calls orchestrator.process_query(message), which triggers the entire AI pipeline.

Step 5: The result comes back as a dictionary with "agent" (which agent answered), "response" (the answer text), and "vector_id".

Step 6: This is returned to the frontend as JSON.

Key code:

```python
orchestrator = Orchestrator(vector_id=vector_id)
result = await orchestrator.process_query(chat_msg.message)
return ChatResponse(
    agent=result["agent"],
    response=result["response"],
    vector_id=vector_id
)
```

---

## 4. The Orchestrator -- The Traffic Controller

File: backend/app/ai/orchestrator.py

The Orchestrator is the brain of the routing system. It does NOT answer questions itself -- it decides WHICH agent should answer.

### 4.1 AgentType Enum

The system defines 4 agent types as an Enum (a fixed list of choices):

```python
class AgentType(str, Enum):
    DISCHARGE = "Discharge Summary Agent"
    BILL = "Bill Validator Agent"
    MEDICINE = "Medicine Price Comparison Agent"
    DIET = "Diet & Nutrition Agent"
```

### 4.2 Initialization

When an Orchestrator is created, it:
1. Stores the vector_id (which document we're working with)
2. Creates its own LLM instance with temperature=0.0 (zero creativity, maximum precision for classification)
3. Initializes the available agents (currently only Discharge and Diet are implemented)

```python
def __init__(self, vector_id: str):
    self.vector_id = vector_id
    self.llm = get_llm(temperature=0.0)
    self.agents = {
        AgentType.DISCHARGE: DischargeSummaryAgent(vector_id),
        AgentType.DIET: DietPlanningAgent(vector_id),
    }
```

### 4.3 Query Classification (_classify_query)

This is the most important method. It takes the user's question and asks Google Gemini to classify it.

The prompt it sends to Gemini looks like this:

```
You are a query router. Your job is to select the best agent.

Available Agents:
1. Diet & Nutrition Agent: For food, diet plans, nutrition, what to eat/avoid
2. Discharge Summary Agent: For everything else. Diagnosis, treatment, reports...

User Query: "What medicines were prescribed?"

Instructions:
- Return ONLY the exact name of the agent.
- Do not add any explanation or punctuation.

Agent Name:
```

Gemini responds with just the agent name, like "Discharge Summary Agent".

If Gemini gives an unexpected response, the system falls back to keyword matching:
- If "diet", "food", "eat", "meal", or "nutrition" appears in the query -> Diet Agent
- Otherwise -> Discharge Agent (the default catch-all)

### 4.4 Query Processing (process_query)

This is the main method called by chat.py. It:
1. Calls _classify_query to determine the right agent
2. Gets the agent object from the dictionary
3. Calls agent.process_async(query) to get the actual answer
4. Returns a dictionary with the query, agent name, and response

```python
async def process_query(self, query: str):
    agent_type = await self._classify_query(query)
    agent = self.agents[agent_type]
    response = await agent.process_async(query)
    return {
        "query": query,
        "agent": agent_type.value,
        "response": response
    }
```

---

## 5. The BaseAgent -- Shared DNA of All Agents

File: backend/app/ai/agents/base.py

Every agent inherits from BaseAgent. This class provides two core capabilities that all agents need:
1. The ability to SEARCH documents (via FAISS vector store)
2. The ability to ASK the LLM a question (via Google Gemini)

### 5.1 get_llm() Function

This creates a connection to Google Gemini via LangChain:

```python
def get_llm(temperature=None):
    from langchain_google_genai import ChatGoogleGenerativeAI
    return ChatGoogleGenerativeAI(
        model=LLM_MODEL,           # "gemini-2.5-flash"
        google_api_key=GOOGLE_API_KEY,
        temperature=temperature or LLM_TEMPERATURE,  # 0.3 by default
    )
```

Temperature controls creativity: 0 = very precise/deterministic, 1 = very creative/random. For medical use, 0.3 is a safe middle ground.

### 5.2 format_search_results() Function

Takes raw search results from FAISS and formats them as numbered text blocks:

```
[1] Patient was diagnosed with Type 2 Diabetes...
   (Source: discharge_report.pdf, Page 3)

[2] Prescribed Metformin 500mg twice daily...
   (Source: discharge_report.pdf, Page 5)
```

This formatted text is then inserted into the LLM prompt so Gemini can reference it.

### 5.3 BaseAgent Class

The constructor takes a vector_id and creates an LLM instance:

```python
class BaseAgent:
    def __init__(self, vector_id: str):
        self.vector_id = vector_id
        self.llm = get_llm()
```

### 5.4 Search Methods

BaseAgent provides specialized search methods for different data sources:

Per-Document Searches (scoped to the user's uploaded document):
- search_discharge_async(query) -- Searches for discharge-type content
- search_bills_async(query) -- Searches for bill-type content

Shared Knowledge Base Searches (global data shared across all users):
- search_regulations_async(query) -- Searches NPPA/CGHS regulations
- search_dietary_async(query) -- Searches dietary guidelines
- search_insurance_async(query) -- Searches insurance policies

All of these ultimately call the FAISS vector store with the user's query.

### 5.5 LLM Methods

- ask_llm_async(prompt) -- Sends a prompt to Gemini and returns the text response
- ask_llm(prompt) -- Same but synchronous

---

## 6. Agent 1: Discharge Summary Agent (FULLY IMPLEMENTED)

File: backend/app/ai/agents/discharge_agent.py

This is the primary agent. It uses RAG (Retrieval-Augmented Generation) to answer medical questions about discharge documents.

### 6.1 System Prompt

Every agent has a personality defined by its SYSTEM_PROMPT:

```
You are a helpful medical assistant specializing in explaining
discharge summaries to patients. Your role is to:
1. Explain medical terms in simple, easy-to-understand language
2. Provide clear summaries of diagnoses, treatments, and medications
3. Highlight important follow-up instructions
4. ALWAYS cite the source document when providing information

Important guidelines:
- Be empathetic and reassuring
- Avoid causing unnecessary alarm
- Recommend consulting a doctor for medical advice
- Always mention page numbers and document sources
```

### 6.2 Main Method: process_async(query)

This is the RAG pipeline in action:

Step 1 - RETRIEVE: Search the FAISS index for the 5 most relevant text chunks from the uploaded document.

```python
results = await self.search_discharge_async(query, k=5)
```

Step 2 - AUGMENT: Format those chunks into readable context text.

```python
context = format_search_results(results)
```

Step 3 - GENERATE: Combine the system prompt + retrieved context + user question into one big prompt, and send it to Gemini.

```python
prompt = f"""{self.SYSTEM_PROMPT}

## Patient's Discharge Documents:
{context}

## Patient's Question:
{query}

## Instructions:
Based on the discharge documents above, answer the patient's question.
Be thorough but easy to understand. Always cite the source.

## Response:"""

response = await self.ask_llm_async(prompt)
```

### 6.3 Special Methods

get_summary(): Searches for 6 key topics (diagnosis, medications, procedures, follow-up, diet, restrictions) across the document, deduplicates results, and asks Gemini to create a comprehensive summary with sections for Diagnosis, Treatment, Medications, Follow-up, Dietary Recommendations, and Warning Signs.

extract_medications(): Specifically searches for medication-related text and asks Gemini to produce a formatted table of all medicines with columns: Medication Name, Dosage, Frequency, and Purpose.

---

## 7. Agent 2: Diet and Nutrition Agent (FULLY IMPLEMENTED)

File: backend/app/ai/agents/diet_agent.py

This agent creates personalized dietary advice based on the patient's medical condition.

### 7.1 System Prompt

```
You are a certified nutritionist who helps patients maintain
a healthy diet after hospital discharge. Your role is to:
1. Analyze the patient's medical condition from discharge documents
2. Consider dietary restrictions based on diagnosis
3. Account for medication-food interactions
4. Create practical, personalized meal plans

Important guidelines:
- Prioritize Indian cuisine options when not specified otherwise
- Be specific about portion sizes
- Mention timing of meals relative to medications
```

### 7.2 Main Method: process_async(query)

This agent searches TWO sources simultaneously:

Step 1 - Search the patient's discharge document for medical conditions:

```python
discharge_results = await self.search_discharge_async(
    "diagnosis condition disease medication", k=5
)
```

Step 2 - Search the shared dietary guidelines knowledge base:

```python
diet_results = await self.search_dietary_async(query, k=5)
```

Step 3 - Combine both contexts and send to Gemini:

```python
prompt = f"""{self.SYSTEM_PROMPT}

## Patient's Medical Information (from discharge):
{discharge_context}

## Relevant Dietary Guidelines:
{diet_context}

## Patient's Question:
{query}

## Instructions:
Based on the medical information and dietary guidelines, provide
personalized advice. Consider:
- The patient's diagnosis and any dietary restrictions
- Medications that may interact with foods

## Response:"""
```

### 7.3 Special Methods

generate_meal_plan(days=7): Creates a 7-day meal plan with table format (Day, Breakfast, Mid-Morning, Lunch, Evening Snack, Dinner), plus hydration guidelines, timing notes, and a shopping list.

foods_to_avoid(): Generates a table of foods/substances the patient should avoid, including the reason, severity (High/Medium/Low), and medication-food interactions.

---

## 8. Agent 3: Bill Validator Agent (PLACEHOLDER)

File: backend/app/ai/agents/bill_agent.py

Current content: Just a comment "# Bill Validator Agent". This agent is not yet implemented.

When built, it would:
- Extract itemized charges from hospital bills
- Cross-reference with CGHS/NPPA price caps (via search_regulations_async)
- Identify overcharges or billing errors
- Compare with insurance policy limits (via search_insurance_async)

---

## 9. Agent 4: Medicine Price Agent (PLACEHOLDER) + Pharmacy Scraper

### 9.1 The Agent (Placeholder)

File: backend/app/ai/agents/medicine_agent.py

Current content: Just a comment "# Medicine Price Comparison Agent". Not yet implemented.

### 9.2 The Pharmacy Scraper (FULLY IMPLEMENTED)

File: backend/app/ai/scrapers/pharmacy.py

Even though the agent is a placeholder, the web scraping tool is fully built. It searches three Indian pharmacy websites in parallel:

Platform 1 -- Tata 1mg (search_1mg):
- URL: https://www.1mg.com/search/all?name={query}
- Scrapes product links containing /drugs/ or /otc/
- Extracts medicine name, price, and URL

Platform 2 -- Apollo Pharmacy (search_apollo):
- URL: https://www.apollopharmacy.in/search-medicines?q={query}
- Scrapes links containing /medicine/
- Same extraction pattern

Platform 3 -- PharmEasy (search_pharmeasy):
- URL: https://pharmeasy.in/search/all?name={query}
- Scrapes links containing /online-medicine-order/
- Same extraction pattern

All three run in parallel using ThreadPoolExecutor:

```python
AGENTS = {
    "tata_1mg": search_1mg,
    "apollo": search_apollo,
    "pharmeasy": search_pharmeasy,
}

def compare_prices(query, limit_per_source=5):
    results = []
    with ThreadPoolExecutor(max_workers=len(AGENTS)) as executor:
        futures = {
            executor.submit(fn, query, limit_per_source): name
            for name, fn in AGENTS.items()
        }
        for fut in as_completed(futures):
            data = fut.result()
            results.extend(data)
    return results
```

Helper functions:
- get_best_price(results) -- Finds the cheapest option across all platforms
- get_medicine_prices_tool(medicine_name) -- Formatted output ready for an LLM agent to use

---

## 10. The Vector Store -- How Agents Search Documents

File: backend/app/ai/vectorstore/store.py

This is the search engine behind every agent's search method.

### 10.1 DocumentVectorStore (Per-Document)

Each uploaded document gets its own FAISS index stored at:
data/vectors/{vector_id}/faiss_index/

It contains two files:
- index.faiss -- The actual FAISS index (binary, contains the number arrays)
- metadata.json -- The text content and metadata for each chunk

Adding documents:
1. Receive text chunks from processor.py
2. Generate embeddings using the embedding model
3. Add the number arrays to the FAISS index
4. Store the original text + metadata in the JSON file
5. Save both files to disk

Searching:
1. Convert the user's query into an embedding (384 numbers)
2. FAISS finds the K closest vectors using L2 (Euclidean) distance
3. Return the original text chunks + metadata for those vectors

### 10.2 SharedVectorStore (Global Knowledge Bases)

Three shared stores exist for all users:
- regulations -- NPPA/CGHS price caps and medical regulations
- dietary -- Dietary guidelines and nutrition data
- insurance -- Insurance policy information

These work identically to DocumentVectorStore but are shared.

---

## 11. The Embedding Engine

File: backend/app/ai/vectorstore/embeddings.py

This module converts human text into 384-dimensional number arrays.

Model used: all-MiniLM-L6-v2 (a pre-trained model from Hugging Face)

How it works:
- The model is lazy-loaded (only loads into memory when first used, taking about 30 seconds)
- embed_texts(["Hello", "World"]) returns [[0.23, -0.45, ...], [0.12, 0.67, ...]]
- Similar texts produce similar number arrays
- "heart surgery" and "cardiac operation" would produce very close arrays
- "heart surgery" and "chocolate cake" would produce very different arrays

The embedding dimension (384) is hardcoded to avoid loading the model just to check its size:

```python
_EMBEDDING_DIM = 384

def get_embedding_dimension():
    return _EMBEDDING_DIM
```

---

## 12. End-to-End Flow Walkthrough

Let us trace a complete example from start to finish.

User's question: "What diet should I follow after my surgery?"

### Step 1: Frontend sends request
POST http://localhost:8000/chat/vec_abc123
Body: {"message": "What diet should I follow after my surgery?"}
Header: Authorization: Bearer eyJ...

### Step 2: chat.py receives the request
- Extracts vector_id = "vec_abc123"
- Verifies the user owns this document in MongoDB
- Creates: orchestrator = Orchestrator(vector_id="vec_abc123")
- Calls: result = await orchestrator.process_query("What diet should I follow...")

### Step 3: Orchestrator classifies the query
- Sends prompt to Gemini: "Which agent should handle this?"
- Gemini responds: "Diet & Nutrition Agent"
- Falls back to keyword matching if needed (query contains "diet")
- Selected: AgentType.DIET

### Step 4: DietPlanningAgent.process_async() is called

### Step 5: Agent searches the discharge document
- Calls search_discharge_async("diagnosis condition disease medication", k=5)
- BaseAgent calls search_document_async("vec_abc123", query, 5, doc_type="discharge")
- DocumentVectorStore loads the FAISS index from data/vectors/vec_abc123/
- The query is embedded into 384 numbers
- FAISS finds the 5 closest text chunks
- Returns chunks like: "Patient underwent appendectomy. Diagnosis: Acute appendicitis..."

### Step 6: Agent searches shared dietary guidelines
- Calls search_dietary_async("What diet should I follow after my surgery?", k=5)
- SharedVectorStore loads the dietary index from data/shared/dietary_index/
- Same embedding + FAISS search process
- Returns chunks like: "Post-surgical diet: Start with clear liquids..."

### Step 7: Agent builds the final prompt
- Combines: System Prompt + Discharge Context + Dietary Context + User Question
- Sends this ~2000-word prompt to Google Gemini

### Step 8: Gemini generates the answer
- Gemini reads all the context and produces a personalized response
- Example: "Based on your appendectomy, here is a recommended diet plan..."

### Step 9: Response travels back
- DietPlanningAgent returns the response string
- Orchestrator wraps it: {"agent": "Diet & Nutrition Agent", "response": "..."}
- chat.py returns it as JSON to the frontend
- Frontend renders the markdown response in the chat interface

---

## 13. Summary Table of All Components

### Agents Status

| Agent | File | Status | Purpose |
|-------|------|--------|---------|
| Discharge Summary | discharge_agent.py | IMPLEMENTED | Medical Q&A about reports |
| Diet & Nutrition | diet_agent.py | IMPLEMENTED | Personalized diet plans |
| Bill Validator | bill_agent.py | PLACEHOLDER | Detect billing errors |
| Medicine Price | medicine_agent.py | PLACEHOLDER | Compare medicine prices |

### Supporting Components

| Component | File | Purpose |
|-----------|------|---------|
| Orchestrator | orchestrator.py | Routes queries to the right agent |
| BaseAgent | base.py | Shared search + LLM capabilities |
| Vector Store | store.py | FAISS index management per document |
| Embeddings | embeddings.py | Text to 384-dim vectors |
| Pharmacy Scraper | pharmacy.py | Web scraping for medicine prices |
| Processor | processor.py | PDF text extraction and chunking |
| PDF-to-Word | pdf_to_word.py | Creates downloadable Word documents |

### Data Flow Summary

| Step | Component | Action |
|------|-----------|--------|
| 1 | Frontend | Sends chat message to backend |
| 2 | chat.py | Validates user, creates Orchestrator |
| 3 | Orchestrator | Asks Gemini which agent to use |
| 4 | Selected Agent | Searches FAISS for relevant chunks |
| 5 | embeddings.py | Converts query to 384-dim vector |
| 6 | store.py | FAISS finds nearest neighbors |
| 7 | Selected Agent | Builds prompt with context |
| 8 | Google Gemini | Generates human-readable answer |
| 9 | chat.py | Returns JSON response to frontend |
