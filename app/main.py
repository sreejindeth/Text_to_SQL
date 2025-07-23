# app/main.py

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
# Import sqlite3 module
import sqlite3 # ADDED: Import sqlite3
# Import CORS middleware
from fastapi.middleware.cors import CORSMiddleware # <-- Added Import
from sqlalchemy import text
from sqlalchemy.orm import Session
import time
from typing import List, Dict, Any
import logging
# import io
# import base64

from app.database import get_db
from app.schemas import QuestionRequest, SQLResponse, QueryResult
from app.utils.data_loader import initialize_database, get_table_info
from app.utils.text_to_sql import TextToSQLAgent
from app.utils.visualizer import determine_chart_type_and_generate

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="E-commerce AI Agent", version="1.0.0")

# Configure CORS settings
origins = [
    "*",  # Allows all origins - suitable for development.
          # For production, specify your frontend URL(s), e.g.,
          # "http://localhost:3000", "https://yourdomain.com"
] # <-- Fixed comment formatting

app.add_middleware(
    CORSMiddleware, # <-- This should now work
    allow_origins=origins, # List of allowed origins
    allow_credentials=True, # Allow cookies/sessions if needed
    allow_methods=["*"], # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"], # Allow all headers (like Content-Type)
)


# Global variables
text_to_sql_agent = None
table_info = None

@app.on_event("startup")
async def startup_event():
    """Initialize database and AI agent on startup"""
    global text_to_sql_agent, table_info
    logger.info("Initializing application...")

    try:
        # Initialize database with CSV files
        engine = initialize_database()
        logger.info("Database initialized.")

        # Get table information
        table_info = get_table_info(engine)
        logger.info(f"Schema loaded: {list(table_info.keys())}")

        # Initialize AI agent
        text_to_sql_agent = TextToSQLAgent(table_info)
        logger.info("AI Agent (Gemini) initialized.")
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        # Depending on requirements, you might want to exit or handle gracefully
        raise e

@app.get("/")
async def root():
    return {"message": "E-commerce AI Agent API", "status": "running"}

@app.get("/schema")
async def get_schema():
    """Get database schema information"""
    return {"tables": table_info}

@app.post("/generate-sql", response_model=SQLResponse)
async def generate_sql(request: QuestionRequest):
    """Generate SQL from natural language question"""
    if not text_to_sql_agent:
        raise HTTPException(status_code=500, detail="AI Agent not initialized")

    try:
        sql_query = text_to_sql_agent.generate_sql_query(request.question)
        return SQLResponse(sql_query=sql_query, question=request.question)
    except Exception as e:
         logger.error(f"Error in /generate-sql: {e}")
         raise HTTPException(status_code=500, detail=f"Failed to generate SQL: {str(e)}")

@app.post("/ask", response_model=QueryResult) # Changed endpoint name to be more intuitive
async def ask_question(request: QuestionRequest, db: Session = Depends(get_db)):
    """Generate SQL, execute it, and return results"""
    if not text_to_sql_agent:
        raise HTTPException(status_code=500, detail="AI Agent not initialized")

    start_time = time.time()
    sql_query = "" # Initialize sql_query for error handling
    try:
        # 1. Generate SQL
        sql_query = text_to_sql_agent.generate_sql_query(request.question)

        # 2. Execute Query
        logger.info(f"Executing query: {sql_query}")
        result = db.execute(text(sql_query))
        rows = result.fetchall()
        execution_time = time.time() - start_time

        # 3. Process Results
        columns = result.keys()
        results = [dict(zip(columns, row)) for row in rows]
        
        # 4. Generate Chart Data (Bonus)
        chart_data, chart_type = determine_chart_type_and_generate(request.question, results)

        # 5. Prepare Response (Bonus: Add chart data if applicable)
        response_data = {
            "question": request.question,
            "sql_query": sql_query,
            "results": results,
            "execution_time": execution_time,
             "chart_data": chart_data, # From visualizer
            "chart_type": chart_type
        }

        return QueryResult(**response_data)
    
    except ValueError as ve: # Catch specific errors from the LLM agent (like invalid SQL start)
        logger.error(f"LLM Generation Error for question '{request.question}': {ve}")
        raise HTTPException(status_code=400, detail=f"Failed to generate a valid SQL query: {str(ve)}")
    except sqlite3.OperationalError as db_err: # Catch specific database errors
         logger.error(f"Database Execution Error for query '{sql_query}' (question: {request.question}): {db_err}") # sql_query is now defined
         raise HTTPException(status_code=400, detail=f"Database error executing query: {str(db_err)}")
    except Exception as e:
        logger.error(f"Unexpected Error in /ask for question '{request.question}': {e}", exc_info=True) # Log full traceback
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {str(e)}") # Generic 500 for unexpected issues

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "ai_agent_ready": text_to_sql_agent is not None}

# Optional: Streaming endpoint (more complex)
# @app.post("/ask-stream")
# async def ask_question_streamed(request: QuestionRequest, background_tasks: BackgroundTasks):
#     # Implementation for streaming chunks (SQL, results, final)
#     # Would use yield and Server-Sent Events (SSE) or WebSockets
#     pass