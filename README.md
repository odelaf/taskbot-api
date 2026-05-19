# TaskBot API

FastAPI + SQLite para gestionar tareas desde iOS Shortcuts.

## Deploy en Render

1. Conectar repo → Python Web Service
2. Build: `pip install -r requirements.txt`
3. Start: `uvicorn api:app --host 0.0.0.0 --port $PORT`
4. Agregar Disk: `/app/data` (1GB)
