import pandas as pd
from sqlalchemy import create_engine, MetaData
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_csv_to_db(csv_path: str, table_name: str, engine):
    """Load CSV data into SQLite database"""
    try:
        if not os.path.exists(csv_path):
            logger.error(f"CSV file not found: {csv_path}")
            return False
        df = pd.read_csv(csv_path)
        logger.info(f"Loaded {len(df)} rows from {csv_path}")
        # Handle potential data type issues automatically
        df.to_sql(table_name, engine, if_exists='replace', index=False, method='multi')
        logger.info(f"Data loaded to table: {table_name}")
        return True
    except Exception as e:
        logger.error(f"Error loading {csv_path} into {table_name}: {str(e)}")
        return False

def initialize_database(data_folder: str = "data"):
    """Initialize database with CSV data"""
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app/ecommerce.db")
    engine = create_engine(DATABASE_URL)

    # Define your CSV files and corresponding table names
    csv_files_and_tables = [
        (os.path.join(data_folder, "ad_sales.csv"), "ad_sales"),
        (os.path.join(data_folder, "total_sales.csv"), "total_sales"),
        (os.path.join(data_folder, "eligibility.csv"), "eligibility")
        # Add more if needed
    ]

    success_count = 0
    for csv_path, table_name in csv_files_and_tables:
        if load_csv_to_db(csv_path, table_name, engine):
            success_count += 1

    if success_count == len(csv_files_and_tables):
        logger.info("All data loaded successfully!")
    else:
        logger.warning(f"Only {success_count}/{len(csv_files_and_tables)} files loaded.")

    return engine

def get_table_info(engine):
    """Get information about tables in database"""
    metadata = MetaData()
    metadata.reflect(bind=engine)

    table_info = {}
    for table_name in metadata.tables:
        table = metadata.tables[table_name]
        # Get column names and types as strings
        columns = [(col.name, str(col.type)) for col in table.columns]
        table_info[table_name] = columns

    return table_info