"""Celery Worker 应用 — AI数字名片"""
from celery import Celery

app = Celery("ai_digital_card")
app.config_from_object({
    "broker_url": "redis://localhost:***@app.task(bind=True, name="debug_task")
def debug_task(self):
    print(f"CELERY WORKER STARTED: {self.request!r}")
    return {"status": "ok", "worker": "ai-digital-card"}
