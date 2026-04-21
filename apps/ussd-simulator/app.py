import os
from uuid import uuid4

import requests
from flask import Flask, render_template_string, request, session

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "agri-trust-ussd-demo")
BACKEND_URL = "http://localhost:8080/api/v1/ussd/session"

PRESETS = []


TEMPLATE = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>AgriTrust USSD Simulator</title>
    <style>
      :root {
        --bg: #f0eadb;
        --panel: rgba(255,250,240,0.9);
        --text: #223126;
        --muted: #5e655a;
        --accent: #2b5e45;
        --gold: #9d6d20;
        --border: rgba(34,49,38,0.12);
        --shadow: 0 24px 60px rgba(69,53,22,0.14);
      }
      * { box-sizing: border-box; }
      body {
        margin: 0;
        font-family: "Segoe UI", system-ui, sans-serif;
        color: var(--text);
        background:
          radial-gradient(circle at top left, rgba(43,94,69,0.18), transparent 28%),
          linear-gradient(180deg, #f7f1e3 0%, var(--bg) 100%);
      }
      .shell {
        max-width: 1180px;
        margin: 0 auto;
        padding: 28px 18px 42px;
      }
      .hero { margin-bottom: 22px; }
      .eyebrow {
        text-transform: uppercase;
        letter-spacing: 0.16em;
        font-size: 0.78rem;
        font-weight: 700;
        color: var(--gold);
      }
      h1 {
        margin: 8px 0 10px;
        font-size: clamp(2.4rem, 5vw, 4rem);
        line-height: 0.98;
      }
      .hero p { max-width: 720px; color: var(--muted); }
      .layout {
        display: grid;
        grid-template-columns: minmax(320px, 0.95fr) minmax(360px, 1.15fr);
        gap: 18px;
      }
      .panel {
        background: var(--panel);
        border-radius: 28px;
        border: 1px solid var(--border);
        box-shadow: var(--shadow);
        padding: 22px;
        backdrop-filter: blur(8px);
      }
      .panel h2 {
        margin-top: 0;
        margin-bottom: 6px;
        font-size: 1.6rem;
      }
      .muted { color: var(--muted); }
      .field { margin-bottom: 14px; }
      .field label {
        display: block;
        margin-bottom: 6px;
        font-size: 0.88rem;
        font-weight: 600;
        color: var(--muted);
      }
      input, button {
        width: 100%;
        border-radius: 16px;
        border: 1px solid var(--border);
        padding: 13px 14px;
        font: inherit;
      }
      input {
        background: rgba(255,255,255,0.88);
      }
      .actions, .preset-grid {
        display: grid;
        gap: 10px;
      }
      .actions {
        grid-template-columns: 1fr 1fr;
        margin-top: 14px;
      }
      button {
        cursor: pointer;
        font-weight: 700;
        background: linear-gradient(180deg, #2e6647, #234c36);
        color: white;
      }
      button.secondary {
        background: rgba(255,255,255,0.84);
        color: var(--accent);
      }
      .preset-grid {
        grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        margin-top: 16px;
      }
      .preset {
        display: inline-flex;
        justify-content: center;
        align-items: center;
        min-height: 60px;
        text-align: center;
      }
      .phone {
        min-height: 720px;
        background:
          linear-gradient(180deg, rgba(17,23,18,0.96), rgba(10,14,12,1)),
          #111;
        color: #f4f7f2;
        border-radius: 34px;
        padding: 18px;
        position: relative;
        overflow: hidden;
      }
      .speaker {
        width: 120px;
        height: 8px;
        border-radius: 999px;
        background: rgba(255,255,255,0.18);
        margin: 0 auto 18px;
      }
      .screen {
        border-radius: 26px;
        background:
          radial-gradient(circle at top, rgba(49,98,65,0.34), transparent 32%),
          linear-gradient(180deg, #1a241d 0%, #0e1511 100%);
        min-height: 640px;
        padding: 16px;
      }
      .ussd-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.9rem;
        margin-bottom: 16px;
      }
      .tag {
        padding: 6px 10px;
        border-radius: 999px;
        background: rgba(255,255,255,0.08);
        color: #d9e9da;
      }
      .response-box {
        white-space: pre-wrap;
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 18px;
        padding: 16px;
        min-height: 180px;
        margin-bottom: 16px;
      }
      .crumbs {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin: 12px 0 16px;
      }
      .crumb {
        padding: 6px 10px;
        border-radius: 999px;
        background: rgba(255,255,255,0.09);
        font-size: 0.82rem;
      }
      .timeline {
        display: flex;
        flex-direction: column;
        gap: 12px;
      }
      .entry {
        border-radius: 16px;
        padding: 14px;
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.08);
      }
      .entry small {
        display: block;
        color: #b4c9b4;
        margin-bottom: 8px;
      }
      .error {
        padding: 12px 14px;
        border-radius: 14px;
        background: rgba(194,73,56,0.16);
        color: #ffd5cf;
        border: 1px solid rgba(194,73,56,0.3);
        margin-top: 14px;
      }
      .activeCard { borderColor: "#2f6f42", borderWidth: 2, backgroundColor: "#f9fff7" }
      .credits {
        margin-top: 48px;
        text-align: center;
        font-size: 0.88rem;
        color: var(--muted);
        opacity: 0.8;
        padding: 24px 0;
        border-top: 1px solid var(--border);
      }
      .credits a {
        color: var(--accent);
        font-weight: 700;
        text-decoration: none;
      }
      .credits a:hover {
        text-decoration: underline;
      }
    </style>
    <script>
      function applyPreset(value) {
        document.getElementById("text").value = value;
      }
    </script>
  </head>
  <body>
    <main class="shell">
      <section class="hero">
        <div class="eyebrow">AgriTrust Telecom</div>
        <h1>AgriTrust telecom console</h1>
        <p>Manage and monitor active USSD sessions, test platform flows, and verify response logic exactly as a gateway would process it.</p>
      </section>

      <section class="layout">
        <section class="panel">
          <h2>Dial Session</h2>
          <p class="muted">Use cumulative text just like a telecom aggregator. Example: <strong>2*Maize*500*A*Harare</strong></p>
          <form method="post">
            <div class="field">
              <label>Session ID</label>
              <input name="session_id" value="{{ session_id }}" placeholder="active-session" />
            </div>
            <div class="field">
              <label>Phone Number</label>
              <input name="phone_number" value="{{ phone_number }}" placeholder="+263771234567" />
            </div>
            <div class="field">
              <label>USSD Text</label>
              <input id="text" name="text" value="{{ text }}" placeholder="1 or 2*Maize*500*A*Harare" />
            </div>
            <div class="actions">
              <button type="submit" name="action" value="send">Send to Backend</button>
              <button type="submit" name="action" value="reset" class="secondary">Reset Session</button>
            </div>
          </form>

          <div class="preset-grid">
            {% for label, value in presets %}
            <button type="button" class="preset secondary" onclick="applyPreset('{{ value }}')">{{ label }}</button>
            {% endfor %}
          </div>

          {% if error %}
          <div class="error">{{ error }}</div>
          {% endif %}
        </section>

        <section class="phone">
          <div class="speaker"></div>
          <div class="screen">
            <div class="ussd-header">
              <strong>*123#</strong>
              <span class="tag">{{ phone_number }}</span>
            </div>
            <div class="response-box">{{ response or "No response yet. Send a request to start the session." }}</div>

            <div class="crumbs">
              {% if crumbs %}
                {% for crumb in crumbs %}
                <span class="crumb">{{ crumb }}</span>
                {% endfor %}
              {% else %}
                <span class="crumb">Awaiting first input</span>
              {% endif %}
            </div>

            <div class="timeline">
              {% for item in history %}
              <div class="entry">
                <small>Input: {{ item.text or "(blank / initial dial)" }}</small>
                <div>{{ item.response }}</div>
              </div>
              {% endfor %}
            </div>
          </div>
        </section>
      </section>
      
      <footer class="credits">
        Developed by <a href="https://linkedin.com/in/mathew-mabira-24861632b" target="_blank">Mathew Mabira</a>
      </footer>
    </main>
  </body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():
    history = session.get("history", [])
    error = ""
    response_text = history[-1]["response"] if history else ""
    session_id = request.form.get("session_id") or session.get("session_id") or "session-live"
    phone_number = request.form.get("phone_number") or session.get("phone_number") or ""

    text = request.form.get("text", "")

    if request.method == "POST":
        action = request.form.get("action", "send")
        if action == "reset":
            session.clear()
            session_id = f"s-{uuid4().hex[:8]}"
            phone_number = ""

            text = ""
            history = []
            response_text = ""
        else:
            payload = {"session_id": session_id, "phone_number": phone_number, "text": text}
            try:
                api_response = requests.post(BACKEND_URL, json=payload, timeout=10)
                api_response.raise_for_status()
                response_text = api_response.json()["message"]
                history = session.get("history", [])
                history.append({"text": text, "response": response_text})
                history = history[-8:]
                session["history"] = history
                session["session_id"] = session_id
                session["phone_number"] = phone_number
            except requests.RequestException as exc:
                error = f"Could not reach FastAPI backend: {exc}"

    crumbs = [part for part in text.split("*") if part]

    return render_template_string(
        TEMPLATE,
        response=response_text,
        error=error,
        session_id=session_id,
        phone_number=phone_number,
        text=text,
        crumbs=crumbs,
        history=history,
        presets=PRESETS,
    )


if __name__ == "__main__":
    app.run(port=5000, debug=True)
