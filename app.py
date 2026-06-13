import os
import threading
import json
from flask import Flask, render_template, request, jsonify, send_file
import io

from database import init_db, create_audit, update_audit, get_audit, list_audits
from models import AuditReport
from modules.visibility import run_visibility_sampling
from modules.competitors import aggregate_competitors
from modules.citations import extract_citations
from modules.grounding import classify_grounding
from modules.evidence import analyze_evidence_gaps
from modules.report import generate_markdown_report

app = Flask(__name__)

os.makedirs("reports", exist_ok=True)
init_db()


def run_audit_pipeline(audit_id: int, brand_name: str, brand_website: str):
    try:
        report = AuditReport(brand_name=brand_name, brand_website=brand_website)

        # Module A — Visibility Sampling
        visibility = run_visibility_sampling(brand_name)
        report.visibility = visibility

        # Module B — Competitor Aggregation
        competitors = aggregate_competitors(visibility, brand_name)
        report.competitors = competitors

        # Module C — Citation Surface
        citations = extract_citations(visibility, brand_website)
        report.citations = citations

        # Module D — Grounding Classification
        grounding = classify_grounding(visibility)
        report.grounding = grounding

        # Module E — Evidence Gap Analyzer
        gaps, quick_wins = analyze_evidence_gaps(
            brand_name, brand_website, visibility, citations, competitors, grounding
        )
        report.evidence_gaps = gaps
        report.quick_wins = quick_wins

        # Generate Markdown Report
        markdown = generate_markdown_report(report)
        report.markdown_report = markdown
        report.status = "complete"

        # Save report to file
        report_path = f"reports/audit_{audit_id}.md"
        with open(report_path, "w") as f:
            f.write(markdown)

        update_audit(
            audit_id,
            status="complete",
            report_json=report.model_dump(exclude={"markdown_report"}),
            markdown_report=markdown,
        )

    except Exception as e:
        update_audit(audit_id, status="failed", report_json={"error": str(e)})


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/audit", methods=["POST"])
def start_audit():
    data = request.get_json()
    brand_name = (data.get("brand_name") or "").strip()
    brand_website = (data.get("brand_website") or "").strip()

    if not brand_name or not brand_website:
        return jsonify({"error": "Brand name and website are required."}), 400

    if not os.environ.get("GEMINI_API_KEY"):
        return jsonify({"error": "GEMINI_API_KEY is not configured. Please add it in Secrets."}), 500

    audit_id = create_audit(brand_name, brand_website)

    thread = threading.Thread(
        target=run_audit_pipeline,
        args=(audit_id, brand_name, brand_website),
        daemon=True,
    )
    thread.start()

    return jsonify({"audit_id": audit_id, "status": "running"})


@app.route("/api/audit/<int:audit_id>", methods=["GET"])
def get_audit_status(audit_id: int):
    audit = get_audit(audit_id)
    if not audit:
        return jsonify({"error": "Audit not found"}), 404
    return jsonify({
        "id": audit["id"],
        "brand_name": audit["brand_name"],
        "brand_website": audit["brand_website"],
        "status": audit["status"],
        "created_at": audit["created_at"],
        "updated_at": audit["updated_at"],
        "has_report": bool(audit.get("markdown_report")),
    })


@app.route("/api/audit/<int:audit_id>/report", methods=["GET"])
def get_report(audit_id: int):
    audit = get_audit(audit_id)
    if not audit:
        return jsonify({"error": "Audit not found"}), 404
    if audit["status"] != "complete":
        return jsonify({"error": "Report not ready"}), 400
    return jsonify({
        "markdown": audit.get("markdown_report", ""),
        "json": audit.get("report_json", {}),
    })


@app.route("/api/audit/<int:audit_id>/download", methods=["GET"])
def download_report(audit_id: int):
    audit = get_audit(audit_id)
    if not audit or audit["status"] != "complete":
        return jsonify({"error": "Report not ready"}), 400
    md = audit.get("markdown_report", "")
    buf = io.BytesIO(md.encode("utf-8"))
    buf.seek(0)
    filename = f"audit_{audit['brand_name'].replace(' ', '_')}_{audit_id}.md"
    return send_file(buf, as_attachment=True, download_name=filename, mimetype="text/markdown")


@app.route("/api/audits", methods=["GET"])
def get_all_audits():
    return jsonify(list_audits())


@app.route("/audit/<int:audit_id>")
def view_audit(audit_id: int):
    return render_template("audit.html", audit_id=audit_id)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
