"""
ClawBot Dashboard — Real-time Web UI

Shows:
- Org chart with live agent status
- Current tasks and who's doing what
- Earnings tracker
- Live activity log
- Task progress

Runs on Flask with Server-Sent Events for real-time updates.
"""

import json
import time
import threading
import os
from flask import Flask, render_template, jsonify, Response, request, stream_with_context

# State that gets updated by the engine
_dashboard_state = {
    "goal": "",
    "agents": {},
    "total_earnings": 0.0,
    "logs": [],
    "elapsed": 0,
}
_state_lock = threading.Lock()
_update_event = threading.Event()


def update_dashboard_state(state_dict: dict):
    """Called by the engine to push state updates."""
    global _dashboard_state
    with _state_lock:
        _dashboard_state = state_dict
    _update_event.set()


def create_app():
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "templates"),
        static_folder=os.path.join(os.path.dirname(__file__), "static"),
    )

    @app.route("/")
    def index():
        return render_template("dashboard.html")

    @app.route("/api/state")
    def get_state():
        with _state_lock:
            return jsonify(_dashboard_state)

    @app.route("/api/stream")
    def stream():
        """Server-Sent Events stream for real-time updates."""
        def event_stream():
            while True:
                _update_event.wait(timeout=2)
                _update_event.clear()
                with _state_lock:
                    data = json.dumps(_dashboard_state)
                yield f"data: {data}\n\n"

        return Response(
            stream_with_context(event_stream()),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    return app


def run_dashboard(port: int = 5050):
    """Start the dashboard server in a background thread."""
    app = create_app()
    thread = threading.Thread(
        target=lambda: app.run(host="0.0.0.0", port=port, debug=False),
        daemon=True,
    )
    thread.start()
    print(f"\n  Dashboard running at: http://localhost:{port}\n")
    return thread
