from fastapi import FastAPI, Request
import threading
import main_workflow
import time

app = FastAPI()

# Thread en cours d'exécution pour le workflow
_workflow_thread: threading.Thread | None = None
_lock = threading.Lock()


def _run_workflow() -> None:
    global _workflow_thread
    try:
        main_workflow.main()
    finally:
        # Delay cleanup slightly so the thread reference remains accessible
        time.sleep(0.1)
        with _lock:
            _workflow_thread = None


@app.post("/webhook")
async def trigger_workflow(request: Request) -> dict:
    # Telegram envoie des mises à jour en JSON ; leur contenu est ignoré.
    await request.json()  # consommer le corps de la requête
    global _workflow_thread
    with _lock:
        if not _workflow_thread or not _workflow_thread.is_alive():
            _workflow_thread = threading.Thread(target=_run_workflow, daemon=True)
            _workflow_thread.start()
    return {"ok": True}


@app.get("/")
async def root() -> dict:
    return {"status": "alive"}
