from fastapi import FastAPI, Request
import threading
import main_workflow

app = FastAPI()

# Flag to avoid running multiple workflows simultaneously
_is_running = False
_lock = threading.Lock()


def _run_workflow() -> None:
    global _is_running
    try:
        main_workflow.main()
    finally:
        with _lock:
            _is_running = False


@app.post("/webhook")
async def trigger_workflow(request: Request) -> dict:
    # Telegram sends JSON updates. We ignore contents and just trigger workflow.
    await request.json()  # read body to consume the request
    global _is_running
    with _lock:
        if not _is_running:
            _is_running = True
            threading.Thread(target=_run_workflow, daemon=True).start()
    return {"ok": True}


@app.get("/")
async def root() -> dict:
    return {"status": "alive"}
