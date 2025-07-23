

### **ecommerce-ai-agent**

An AI-powered API that answers natural language questions about e-commerce data by translating them into SQL queries, executing them against a database populated with your datasets, and returning the results.

#### **Table of Contents**

1.  [Concept](#concept)
2.  [Features](#features)
3.  [Project Structure](#project-structure)
4.  [Prerequisites](#prerequisites)
5.  [Setup](#setup)
6.  [Running the Application](#running-the-application)
7.  [API Endpoints](#api-endpoints)
8.  [Testing the API](#testing-the-api)
9.  [Visualization](#visualization)
10. [Built With](#built-with)
11. [Contributing](#contributing)
12. [License](#license)

---

### **Concept**

This project implements an AI agent that acts as an intermediary between a user's natural language question and structured e-commerce data stored in a SQL database. The core workflow is:

1.  **Data Ingestion:** CSV files containing Product-Level Ad Sales, Total Sales, and Eligibility data are loaded into an in-memory SQLite database upon application startup. Each CSV becomes a table.
2.  **Question Understanding:** A user submits a question (e.g., "What is my total sales?") via an API endpoint.
3.  **SQL Generation:** The application uses the Google Gemini API (specifically `gemini-2.0-flash`) to interpret the natural language question. It provides the LLM with the database schema (table and column names) to guide it in generating an accurate SQL `SELECT` query.
4.  **Query Execution:** The generated SQL query is executed against the local SQLite database.
5.  **Response Formatting:** The results from the database query are packaged into a JSON response. If the data is suitable for charting, basic visualization data (using Plotly) is also generated and included.
6.  **API Delivery:** The structured JSON response is sent back to the user via the API.

This modular approach separates the concerns of data storage, natural language processing, and API communication.

---

### **Features**

*   **Natural Language to SQL:** Converts user questions into executable SQL.
*   **Database Integration:** Uses SQLite for fast, local data querying.
*   **API Access:** Provides a RESTful API using FastAPI for easy interaction.
*   **Visualization (Bonus):** Generates Plotly chart data for certain types of query results.
*   **LLM Integration:** Leverages the Google Gemini API for intelligent query generation.
*   **Interactive Docs:** Includes automatically generated Swagger UI (`/docs`) and ReDoc (`/redoc`) for API exploration.

---

### **Project Structure**

```
ecommerce-ai-agent/
├── app/                    # Main application package
│   ├── __init__.py
│   ├── main.py             # FastAPI application entry point, defines routes
│   ├── database.py         # Database connection setup (SQLAlchemy)
│   ├── models.py           # (Potentially unused) SQLAlchemy ORM models
│   ├── schemas.py          # Pydantic models for request/response validation
│   └── utils/              # Utility functions
│       ├── __init__.py
│       ├── data_loader.py    # Loads CSV data into SQLite database
│       ├── text_to_sql.py    # Contains the TextToSQLAgent class using Gemini
│       └── visualizer.py     # Generates chart data from query results
├── data/                   # Directory for input CSV datasets
│   ├── Product-Level Ad Sales and Metrics (mapped) - Product-Level Ad Sales and Metrics (mapped).csv
│   ├── Product-Level Eligibility Table (mapped) - Product-Level Eligibility Table (mapped).csv
│   └── Product-Level Total Sales and Metrics (mapped) - Product-Level Total Sales and Metrics (mapped).csv
├── .env                    # Environment variables (API keys, DB URL)
├── .gitignore              # Specifies files/folders to ignore in Git
├── requirements.txt        # Python dependencies
├── run.py                  # Script to easily start the FastAPI server
└── README.md               # This file
```

---

### **Prerequisites**

*   **Python 3.8+:** Ensure Python is installed on your system.
*   **Virtual Environment Tool:** `venv` (usually included with Python) or `conda`.
*   **Google AI API Key:** Obtain a free API key from [Google AI Studio](https://aistudio.google.com/). This is required for the LLM functionality.

---

### **Setup**

1.  **Clone the Repository:**
    ```bash
    git clone <your-github-repo-url>
    cd ecommerce-ai-agent
    ```
2.  **Create a Virtual Environment:**
    ```bash
    python -m venv venv
    # Activate it:
    # On Windows:
    venv\Scripts\activate
    # On macOS/Linux:
    source venv/bin/activate
    ```
3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configure Environment Variables:**
    *   Create a file named `.env` in the project root directory.
    *   Add your Google AI API key:
        ```env
        GOOGLE_API_KEY=your_actual_google_ai_api_key_here
        DATABASE_URL=sqlite:///./app/ecommerce.db
        ```
        Replace `your_actual_google_ai_api_key_here` with the key you obtained from Google AI Studio.

5.  **Place Datasets:**
    *   Ensure the three provided CSV files are placed in the `data/` directory.
    *   For easier handling, you might want to rename them to shorter names like `ad_sales.csv`, `total_sales.csv`, and `eligibility.csv` and update the corresponding paths in `app/utils/data_loader.py`.

---

### **Running the Application**

1.  **Ensure Virtual Environment is Activated:** You should see `(venv)` in your terminal prompt.
2.  **Start the Server:**
    ```bash
    python run.py
    ```
3.  **Access the Application:**
    *   The API will be available at `http://localhost:8000`.
    *   Interactive API documentation (Swagger UI) is available at `http://localhost:8000/docs`.
    *   Alternative API documentation (ReDoc) is available at `http://localhost:8000/redoc`.

---

### **API Endpoints**

*   **`GET /`**
    *   **Description:** Root endpoint providing basic status information.
    *   **Response:** `{"message": "E-commerce AI Agent API", "status": "running"}`

*   **`GET /schema`**
    *   **Description:** Retrieves the database schema (table names and column definitions).
    *   **Response:** A JSON object describing the structure of the loaded data.

*   **`POST /ask`**
    *   **Description:** The main endpoint. Accepts a natural language question, generates SQL, executes it, and returns the results.
    *   **Request Body:**
        ```json
        {
          "question": "Your natural language question here"
        }
        ```
    *   **Response:** A JSON object containing the original question, the generated SQL query, the database results, execution time, and optionally chart data/type.
        ```json
        {
          "question": "What is my total sales?",
          "sql_query": "SELECT SUM(total_sales) FROM total_sales;",
          "results": [{"SUM(total_sales)": 1004904.5599999991}],
          "execution_time": 1.03,
          "chart_data": null,
          "chart_type": null
        }
        ```

*   **`GET /health`**
    *   **Description:** Health check endpoint.
    *   **Response:** `{"status": "healthy", "ai_agent_ready": true}`

---

### **Testing the API**

You can test the API using various methods:

1.  **Using `curl` (Terminal):**
    Create JSON files (e.g., `question1.json`) for your questions:
    ```json
    {"question": "What is my total sales?"}
    ```
    Then use `curl`:
    ```bash
    curl -X POST "http://localhost:8000/ask" -H "Content-Type: application/json" -d @question1.json
    ```

2.  **Using the Interactive Docs (`/docs`):**
    *   Navigate to `http://localhost:8000/docs`.
    *   Find the `POST /ask` endpoint.
    *   Click "Try it out".
    *   Enter your JSON question.
    *   Click "Execute".

3.  **Using Postman or Similar Tools:**
    *   Set method to `POST`.
    *   URL: `http://localhost:8000/ask`.
    *   Headers: `Content-Type: application/json`.
    *   Body (raw, JSON): `{"question": "Calculate the RoAS (Return on Ad Spend)."}`.
    *   Send the request.

---

### **Visualization**

*   For queries that return suitable data (e.g., multiple rows with numerical values), the backend attempts to generate chart data.
*   The chart data is returned as a Plotly JSON-compatible dictionary within the `/ask` response under the `chart_data` key.
*   To view the chart, you can use the provided HTML viewers or integrate the `chart_data` into a frontend application using the Plotly.js library.

---

### **Built With**

*   **[FastAPI](https://fastapi.tiangolo.com/)** - Modern, fast (high-performance) web framework for building APIs with Python 3.7+.
*   **[SQLite](https://www.sqlite.org/)** - Lightweight disk-based database.
*   **[SQLAlchemy](https://www.sqlalchemy.org/)** - SQL toolkit and Object-Relational Mapping (ORM) library for Python.
*   **[Pandas](https://pandas.pydata.org/)** - Powerful data manipulation and analysis library.
*   **[Google Generative AI (Gemini)](https://ai.google.dev/)** - For natural language understanding and SQL generation.
*   **[Pydantic](https://docs.pydantic.dev/)** - Data validation and settings management using Python type hints.
*   **[Plotly](https://plotly.com/python/)** - For generating interactive chart data.
*   **[Uvicorn](https://www.uvicorn.org/)** - ASGI server implementation for Python.

---

### **Contributing**

Contributions are welcome! Please fork the repository and submit pull requests.

---

### **License**

This project is licensed under the MIT License - see the `LICENSE` file for details (you should create this file if you plan to specify a license).

---