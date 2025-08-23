import threading
from unittest.mock import patch

import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # type: ignore

import webhook_server


def test_webhook_allows_new_run_after_previous_completed():
    client = TestClient(webhook_server.app)

    with patch("main_workflow.main"):
        # First trigger
        response = client.post("/webhook", json={})
        assert response.json() == {"ok": True}
        t1 = webhook_server._workflow_thread
        assert isinstance(t1, threading.Thread)
        t1.join()
        assert webhook_server._workflow_thread is None

        # Second trigger after previous completion
        response = client.post("/webhook", json={})
        assert response.json() == {"ok": True}
        t2 = webhook_server._workflow_thread
        assert isinstance(t2, threading.Thread)
        t2.join()
