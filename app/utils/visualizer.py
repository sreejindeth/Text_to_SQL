# app/utils/visualizer.py
import matplotlib.pyplot as plt
import matplotlib
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import pandas as pd
import io
import base64
from typing import List, Dict, Any, Tuple, Optional
import logging
# --- Import for serialization fix ---
import numpy as np
from collections.abc import Iterable
# --- End Import for serialization fix ---

# Use non-interactive backend for server-side generation
matplotlib.use('Agg')
logger = logging.getLogger(__name__)

# --- Helper function to make data JSON serializable (ADDED) ---
def make_serializable(obj):
    """
    Recursively converts NumPy types and other non-serializable objects
    within a data structure (dict, list, etc.) to native Python types.
    """
    if isinstance(obj, dict):
        return {key: make_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [make_serializable(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(make_serializable(item) for item in obj)
    elif isinstance(obj, np.integer): # e.g., np.int64
        return int(obj)
    elif isinstance(obj, np.floating): # e.g., np.float64
        return float(obj)
    elif isinstance(obj, np.ndarray):
        # Convert ndarray to list, then make list elements serializable
        return make_serializable(obj.tolist())
    elif isinstance(obj, pd.Series):
         # Convert Series to list, then make serializable
         return make_serializable(obj.tolist())
    elif isinstance(obj, pd.Timestamp):
         # Convert Timestamp to string or ISO format
         return obj.isoformat()
    elif pd.isna(obj): # Handle pandas NaT, NaN etc.
        return None
    # Add more type conversions if needed
    else:
        # For objects that are already serializable (str, int, float, bool, None)
        # or unknown types, try to return as is.
        # Be cautious: unknown complex objects might still cause issues.
        return obj
# --- End Helper function ---

# --- Matplotlib Helper Functions (for static images) ---
# (These functions remain largely unchanged, kept for completeness/future use)
def _create_matplotlib_fig(data: pd.DataFrame, chart_type: str, title: str) -> Optional[plt.Figure]:
    """Creates a matplotlib figure based on data and chart type."""
    fig, ax = plt.subplots(figsize=(10, 6))

    try:
        if chart_type == "bar" and len(data.columns) >= 2:
            x_col, y_col = data.columns[0], data.columns[1]
            ax.bar(data[x_col], data[y_col])
            ax.set_xlabel(x_col)
            ax.set_ylabel(y_col)
        elif chart_type == "line" and len(data.columns) >= 2:
             x_col, y_col = data.columns[0], data.columns[1]
             ax.plot(data[x_col], data[y_col], marker='o')
             ax.set_xlabel(x_col)
             ax.set_ylabel(y_col)
             plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
        elif chart_type == "pie" and len(data.columns) >= 2:
            labels_col, values_col = data.columns[0], data.columns[1]
            filtered_data = data[data[values_col] > 0]
            if not filtered_data.empty:
                ax.pie(filtered_data[values_col], labels=filtered_data[labels_col], autopct='%1.1f%%')
                ax.set_title(title)
            else:
                logger.warning("No positive values for pie chart.")
                plt.close(fig)
                return None
        else:
            logger.warning(f"Unsupported chart type '{chart_type}' or insufficient data columns for Matplotlib.")
            plt.close(fig)
            return None

        ax.set_title(title)
        plt.tight_layout()
        return fig
    except Exception as e:
        logger.error(f"Error creating Matplotlib chart: {e}")
        plt.close(fig)
        return None

def create_matplotlib_chart_base64(data: List[Dict[str, Any]], chart_type: str, title: str) -> Optional[str]:
    """Creates a chart using matplotlib and returns it as a base64 PNG string."""
    if not data:
        return None
    try:
        df = pd.DataFrame(data)
        if df.empty:
             return None

        fig = _create_matplotlib_fig(df, chart_type, title)
        if fig is None:
            return None

        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        return img_base64
    except Exception as e:
        logger.error(f"Error generating Matplotlib chart base64: {e}")
        return None

# --- Plotly Helper Functions (for interactive or static images) ---
def _create_plotly_fig(data: pd.DataFrame, chart_type: str, title: str) -> Optional[go.Figure]:
    """Creates a Plotly figure based on data and chart type."""
    try:
        if chart_type == "bar" and len(data.columns) >= 2:
            x_col, y_col = data.columns[0], data.columns[1]
            fig = px.bar(data, x=x_col, y=y_col, title=title)
        elif chart_type == "line" and len(data.columns) >= 2:
            x_col, y_col = data.columns[0], data.columns[1]
            fig = px.line(data, x=x_col, y=y_col, markers=True, title=title)
        elif chart_type == "pie" and len(data.columns) >= 2:
            labels_col, values_col = data.columns[0], data.columns[1]
            filtered_data = data[data[values_col] > 0]
            if not filtered_data.empty:
                fig = px.pie(filtered_data, values=values_col, names=labels_col, title=title)
            else:
                logger.warning("No positive values for pie chart (Plotly).")
                return None
        elif chart_type == "scatter" and len(data.columns) >= 2:
             x_col, y_col = data.columns[0], data.columns[1]
             fig = px.scatter(data, x=x_col, y=y_col, title=title)
             if len(data.columns) >= 3:
                 size_col = data.columns[2]
                 # Ensure size_col is numeric before scaling
                 if pd.api.types.is_numeric_dtype(data[size_col]):
                     fig.update_traces(marker_size=data[size_col] / data[size_col].max() * 30)
        else:
            logger.warning(f"Unsupported chart type '{chart_type}' or insufficient data columns for Plotly.")
            return None
        return fig
    except Exception as e:
        logger.error(f"Error creating Plotly chart: {e}")
        return None

# --- UPDATED FUNCTION ---
def create_plotly_chart_json(data: List[Dict[str, Any]], chart_type: str, title: str) -> Optional[Dict[str, Any]]:
    """Creates a chart using Plotly and returns it as a JSON-serializable dict (for interactive)."""
    if not data:
        return None
    try:
        df = pd.DataFrame(data)
        if df.empty:
             return None

        fig = _create_plotly_fig(df, chart_type, title)
        if fig is None:
            return None

        # Convert Plotly figure to JSON-compatible dict
        chart_json = fig.to_dict()
        
        # --- CRITICAL FIX: Make the chart data JSON serializable ---
        serializable_chart_data = make_serializable(chart_json)
        # --- END CRITICAL FIX ---
        
        return serializable_chart_data # Return the serializable version
    except Exception as e:
        logger.error(f"Error generating Plotly chart JSON: {e}")
        return None
# --- END UPDATED FUNCTION ---

# (create_plotly_chart_base64 remains largely the same, kept for completeness/future use)
def create_plotly_chart_base64(data: List[Dict[str, Any]], chart_type: str, title: str) -> Optional[str]:
    """Creates a chart using Plotly and returns it as a base64 PNG string."""
    if not data:
        return None
    try:
        df = pd.DataFrame(data)
        if df.empty:
             return None

        fig = _create_plotly_fig(df, chart_type, title)
        if fig is None:
            return None

        img_bytes = pio.to_image(fig, format='png')
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')
        return img_base64
    except Exception as e:
        logger.error(f"Error generating Plotly chart base64: {e}")
        return None

# --- Main Visualization Logic ---
def determine_chart_type_and_generate(question: str, results: List[Dict[str, Any]]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Determines the appropriate chart type based on the question and results,
    and generates the chart data.
    Returns: (chart_data_dict, chart_type_string)
    chart_data_dict can be Plotly JSON or {'image': 'base64string'}
    chart_type_string describes the type (e.g., 'bar', 'line', 'pie')
    """
    if not results:
        return None, None

    question_lower = question.lower()
    num_results = len(results)
    num_columns = len(results[0]) if results else 0

    # --- Determine Chart Type ---
    chart_type = None
    if "trend" in question_lower or "over time" in question_lower:
        chart_type = "line"
    elif num_results == 1 and num_columns == 1:
        pass # Single value, no chart for now
    elif num_results > 1 and num_columns >= 2:
        if "distribution" in question_lower or "proportion" in question_lower:
            chart_type = "pie"
        else:
            chart_type = "bar" # Default for multi-row, multi-column
    elif num_results == 1 and num_columns >= 2:
         chart_type = "bar"
    # Add more rules as needed...

    if not chart_type:
        logger.info("Could not determine a suitable chart type for the results.")
        return None, None

    # --- Generate Chart Data ---
    title = f"Visualization for: {question}"
    chart_data = None

    # Generate Plotly JSON as the primary chart data.
    chart_data = create_plotly_chart_json(results, chart_type, title) # Uses the updated function

    # Fallback logic (commented out as before, but would also use updated functions)
    # if chart_data is None:
    #     chart_data = {"image": create_plotly_chart_base64(results, chart_type, title)}
    #     if chart_data["image"] is None:
    #          chart_data = {"image": create_matplotlib_chart_base64(results, chart_type, title)}

    if chart_data is None:
         logger.info(f"Failed to generate chart data for type '{chart_type}'.")
         return None, chart_type

    logger.info(f"Generated chart data of type '{chart_type}' for question: {question}")
    return chart_data, chart_type
