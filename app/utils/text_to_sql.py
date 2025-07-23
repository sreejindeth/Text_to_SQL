
import google.generativeai as genai
from typing import Dict, List
import os
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

class TextToSQLAgent:
    def __init__(self, table_info: Dict, model_name: str = "gemini-2.0-flash"): # CHANGED: Use a more standard model name
        self.table_info = table_info
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables.")
        genai.configure(api_key=self.api_key)
        # Use the potentially more compatible model name
        self.model = genai.GenerativeModel(model_name) # CHANGED: Removed specific version

    def generate_schema_description(self) -> str:
        """Generate schema description for the AI model"""
        schema_desc = "Database Schema:\n"
        for table_name, columns in self.table_info.items():
            schema_desc += f"\nTable: {table_name}\n"
            for col_name, col_type in columns:
                schema_desc += f"  - {col_name} ({col_type})\n"
        return schema_desc

    def generate_sql_query(self, natural_language_query: str) -> str:
        """Convert natural language to SQL query using Gemini"""
        schema_desc = self.generate_schema_description()

        # --- IMPROVED PROMPT ---
        prompt = f"""
        You are an expert SQL query generator for an e-commerce database. Convert the following natural language question to a SINGLE, valid SQL query for SQLite.

        {schema_desc}

        Important Rules:
        1.  ONLY output the SQL query itself. No explanations, markdown, prefixes like '```sql', or extra text.
        2.  Ensure the query is syntactically correct for SQLite.
        3.  Use the EXACT table and column names provided in the schema.
        4.  For calculations like RoAS (Return on Ad Spend) and CPC (Cost Per Click), use the following formulas and handle division by zero:
            *   RoAS = SUM(ad_sales) / NULLIF(SUM(ad_spend), 0)
            *   CPC = SUM(ad_spend) / NULLIF(SUM(clicks), 0)
            *   Use NULLIF(denominator, 0) to prevent division by zero errors. DO NOT use CASE WHEN for this simple case.
        5.  If the question asks "Which product..." or requests identification, make sure to SELECT the 'item_id'.
        6.  Use appropriate JOINs if data from multiple tables is needed (check schema for relationships, likely on 'item_id' and 'date').
        7.  For date ranges, use the 'date' column.
        8.  Limit results if explicitly requested (e.g., "top 5" -> LIMIT 5).
        9.  Aggregate functions like SUM, AVG should be used if totals/averages are asked.
        10. Double-check your output. It MUST start with SELECT, INSERT, UPDATE, or DELETE.

        Examples:
        Question: What is my total sales?
        SQL Query: SELECT SUM(total_sales) FROM total_sales;

        Question: Calculate the RoAS (Return on Ad Spend).
        SQL Query: SELECT SUM(ad_sales) / NULLIF(SUM(ad_spend), 0) AS RoAS FROM ad_sales;

        Question: Which product had the highest CPC (Cost Per Click)?
        SQL Query: SELECT item_id, SUM(ad_spend) / NULLIF(SUM(clicks), 0) AS CPC FROM ad_sales GROUP BY item_id ORDER BY CPC DESC LIMIT 1;

        Natural Language Question: {natural_language_query}

        SQL Query:
        """
        # --- END IMPROVED PROMPT ---

        try:
            response = self.model.generate_content(prompt)
            # Get the text content from the response object
            raw_sql_query = response.text.strip() if response.text else ""

            # --- IMPROVED CLEANUP ---
            # Basic cleanup if model adds markdown or extra text
            sql_query = raw_sql_query
            if sql_query.lower().startswith("```sql"):
                sql_query = sql_query[6:] # Remove ```sql
            if sql_query.endswith("```"):
                sql_query = sql_query[:-3] # Remove ```
            # Remove any leading/trailing whitespace again
            sql_query = sql_query.strip()

            # --- CRITICAL: Validate it starts with a keyword ---
            valid_start_keywords = ("select", "insert", "update", "delete", "with")
            if not sql_query.lower().startswith(valid_start_keywords):
                 # Log the problematic query for debugging
                 logger.warning(f"LLM generated invalid SQL start for '{natural_language_query}': {raw_sql_query}")
                 # Raise an error or return a default/error query
                 raise ValueError(f"Invalid SQL query generated (doesn't start with SELECT/INSERT/UPDATE/DELETE): {sql_query[:50]}...")
            # --- END IMPROVED CLEANUP ---

            logger.info(f"Generated SQL for '{natural_language_query}': {sql_query}")
            return sql_query
        except Exception as e:
            logger.error(f"Error generating SQL for '{natural_language_query}': {str(e)}")
            # Re-raise the error so the API endpoint can handle it properly
            raise e
        
