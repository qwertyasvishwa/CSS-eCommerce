import os
from datetime import datetime
from typing import Optional, List

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, Response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_, desc


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "chat_archive.sqlite3")


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    return app


app = create_app()
db = SQLAlchemy(app)


class Entry(db.Model):
    __tablename__ = "entries"

    id = db.Column(db.Integer, primary_key=True)
    prompt = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    model = db.Column(db.String(128), nullable=True)
    tags = db.Column(db.String(512), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "prompt": self.prompt,
            "response": self.response,
            "model": self.model,
            "tags": self.tags,
            "created_at": self.created_at.isoformat() + "Z",
        }


@app.before_first_request
def init_db():
    db.create_all()


@app.route("/")
def index():
    recent: List[Entry] = Entry.query.order_by(desc(Entry.created_at)).limit(10).all()
    return render_template("index.html", recent=recent)


@app.route("/add", methods=["POST"])
def add_entry():
    prompt = request.form.get("prompt", "").strip()
    response = request.form.get("response", "").strip()
    model = request.form.get("model", "").strip() or None
    tags = request.form.get("tags", "").strip() or None

    if not prompt or not response:
        flash("Prompt and response are required", "error")
        return redirect(url_for("index"))

    entry = Entry(prompt=prompt, response=response, model=model, tags=tags)
    db.session.add(entry)
    db.session.commit()
    flash("Saved entry", "success")
    return redirect(url_for("entries"))


@app.route("/entries")
def entries():
    q = request.args.get("q", "").strip()
    tag = request.args.get("tag", "").strip()
    start = request.args.get("start", "").strip()
    end = request.args.get("end", "").strip()

    query = Entry.query
    if q:
        query = query.filter(or_(Entry.prompt.ilike(f"%{q}%"), Entry.response.ilike(f"%{q}%")))
    if tag:
        query = query.filter(Entry.tags.isnot(None)).filter(Entry.tags.ilike(f"%{tag}%"))
    if start:
        try:
            start_dt = datetime.fromisoformat(start)
            query = query.filter(Entry.created_at >= start_dt)
        except ValueError:
            flash("Invalid start date. Use ISO format like 2025-09-16 or 2025-09-16T12:00", "error")
    if end:
        try:
            end_dt = datetime.fromisoformat(end)
            query = query.filter(Entry.created_at <= end_dt)
        except ValueError:
            flash("Invalid end date. Use ISO format like 2025-09-16 or 2025-09-16T12:00", "error")

    results = query.order_by(desc(Entry.created_at)).all()
    return render_template("entries.html", entries=results, q=q, tag=tag, start=start, end=end)


@app.route("/entry/<int:entry_id>")
def entry_detail(entry_id: int):
    entry: Optional[Entry] = Entry.query.get_or_404(entry_id)
    return render_template("detail.html", entry=entry)


@app.route("/document")
def document_view():
    entries: List[Entry] = Entry.query.order_by(Entry.created_at.asc()).all()
    return render_template("document.html", entries=entries)


def render_markdown(entries: List[Entry]) -> str:
    lines: List[str] = ["# Chat Archive", ""]
    for e in entries:
        created = e.created_at.strftime("%Y-%m-%d %H:%M")
        header = f"## {created}"
        meta_parts = []
        if e.model:
            meta_parts.append(f"model: {e.model}")
        if e.tags:
            meta_parts.append(f"tags: {e.tags}")
        meta = f"_({' | '.join(meta_parts)})_" if meta_parts else ""
        lines.extend([header, meta, "", "**Prompt**:", "", e.prompt, "", "**Response**:", "", e.response, "", "---", ""])
    return "\n".join(lines).strip() + "\n"


@app.route("/export.md")
def export_md():
    entries: List[Entry] = Entry.query.order_by(Entry.created_at.asc()).all()
    content = render_markdown(entries)
    return Response(content, mimetype="text/markdown", headers={
        "Content-Disposition": "attachment; filename=chat-archive.md"
    })


@app.route("/export.json")
def export_json():
    entries: List[Entry] = Entry.query.order_by(Entry.created_at.asc()).all()
    return jsonify([e.to_dict() for e in entries])


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)

