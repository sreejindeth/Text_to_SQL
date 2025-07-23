import uvicorn
import os

if __name__ == "__main__":
    # Ensure the app directory exists for the database
    os.makedirs("app", exist_ok=True)

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)