from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class QuestionRequest(BaseModel):
    question: str

class SQLResponse(BaseModel):
    sql_query: str
    question: str

class QueryResult(BaseModel):
    question: str
    sql_query: str
    results: List[Dict[str, Any]]
    execution_time: Optional[float] = None
    # Optional: for bonus chart data
    chart_data: Optional[Dict[str, Any]] = None
    chart_type: Optional[str] = None

class StreamChunk(BaseModel):
    # For potential streaming implementation
    type: str # e.g., "sql", "result", "final"
    content: Any