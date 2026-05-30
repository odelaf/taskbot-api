import os
import sys
import uvicorn

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    print(f"DEBUG: PORT env var = {os.getenv('PORT')}", file=sys.stderr)
    print(f"DEBUG: Starting uvicorn on port {port}", file=sys.stderr)
    uvicorn.run("api:app", host="0.0.0.0", port=port)

