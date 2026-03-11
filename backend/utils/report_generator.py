from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _make_score_table(scores: Dict[str, int]) -> Table:
    rows = [["Score", "Value"]]
    for key, value in scores.items():
        label = key.replace("_", " ").title()
        rows.append([label, f"{value}/100"])
    table = Table(rows, colWidths=[95 * mm, 40 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F8FAFC")),
            ]
        )
    )
    return table


def _make_severity_chart(distribution: Dict[str, int]) -> Drawing:
    values = [[
        distribution.get("critical", 0),
        distribution.get("high", 0),
        distribution.get("medium", 0),
        distribution.get("low", 0),
    ]]
    drawing = Drawing(160 * mm, 70 * mm)
    chart = VerticalBarChart()
    chart.x = 10
    chart.y = 10
    chart.height = 48 * mm
    chart.width = 145 * mm
    chart.data = values
    chart.categoryAxis.categoryNames = ["Critical", "High", "Medium", "Low"]
    chart.valueAxis.valueMin = 0
    chart.bars[0].fillColor = colors.HexColor("#2563EB")
    chart.barWidth = 12
    chart.groupSpacing = 14
    drawing.add(chart)
    return drawing


def _top_issues_table(issues: List[Dict], limit: int = 12) -> Table:
    rows = [["Severity", "Type", "File", "Line"]]
    severity_rank = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    ordered = sorted(
        issues,
        key=lambda item: severity_rank.get(str(item.get("severity", "low")).lower(), 0),
        reverse=True,
    )[:limit]
    for issue in ordered:
        rows.append(
            [
                str(issue.get("severity", "")).title(),
                str(issue.get("issue_type", ""))[:42],
                str(issue.get("file_path", ""))[:44],
                str(issue.get("line", "")),
            ]
        )
    table = Table(rows, colWidths=[25 * mm, 48 * mm, 80 * mm, 15 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E1")),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F8FAFC")),
            ]
        )
    )
    return table


def _ai_refactor_table(issues: List[Dict], limit: int = 6) -> Table:
    rows = [["Issue", "Suggested Improvement"]]
    severity_rank = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    ordered = sorted(
        issues,
        key=lambda item: severity_rank.get(str(item.get("severity", "low")).lower(), 0),
        reverse=True,
    )[:limit]
    for issue in ordered:
        issue_name = str(issue.get("issue_type", ""))[:34]
        suggestion = str(issue.get("suggested_code", "")).strip().replace("\n", " ")
        if not suggestion:
            suggestion = str(issue.get("best_practice", "")).strip()
        rows.append([issue_name, suggestion[:120]])

    table = Table(rows, colWidths=[52 * mm, 116 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E1")),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F8FAFC")),
            ]
        )
    )
    return table


def generate_pdf_report(scan_result: Dict, output_file: Path) -> Path:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(output_file), pagesize=A4, leftMargin=20, rightMargin=20, topMargin=24)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleCustom",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#0F172A"),
    )
    subtitle_style = ParagraphStyle(
        "SubtitleCustom",
        parent=styles["Normal"],
        textColor=colors.HexColor("#334155"),
        leading=14,
    )

    totals = scan_result.get("totals", {})
    scores = scan_result.get("scores", {})
    distribution = scan_result.get("severity_distribution", {})
    issues = scan_result.get("issues", [])
    recommendations = scan_result.get("recommendations", [])
    metadata = scan_result.get("metadata", {})
    dependency_score = metadata.get("dependency_risk_score", "-")
    test_score = (metadata.get("test_coverage") or {}).get("test_coverage_score", "-")
    maturity_score = (metadata.get("code_maturity") or {}).get("code_maturity_index", "-")
    ai_mode = metadata.get("ai_mode_applied", "basic")

    story = [
        Paragraph("SecureCode AI Risk & Reliability Report", title_style),
        Spacer(1, 6),
        Paragraph("Executive Summary", styles["Heading2"]),
        Paragraph(
            (
                f"Files scanned: {totals.get('total_files_scanned', 0)} | "
                f"Lines analyzed: {totals.get('total_lines_analyzed', 0)} | "
                f"Issues found: {totals.get('total_issues_found', 0)} | "
                f"AI mode: {ai_mode}"
            ),
            subtitle_style,
        ),
        Paragraph(
            (
                f"Dependency Risk Score: {dependency_score}/100 | "
                f"Test Coverage Score: {test_score}/100 | "
                f"Code Maturity Index: {maturity_score}/100"
            ),
            subtitle_style,
        ),
        Spacer(1, 8),
        _make_score_table(scores),
        Spacer(1, 12),
        Paragraph("Severity Distribution", styles["Heading2"]),
        _make_severity_chart(distribution),
        Spacer(1, 10),
        Paragraph("Top Risk Findings", styles["Heading2"]),
        _top_issues_table(issues),
        Spacer(1, 10),
        Paragraph("AI Refactor Suggestions", styles["Heading2"]),
        _ai_refactor_table(issues),
        Spacer(1, 10),
        Paragraph("Improvement Recommendations", styles["Heading2"]),
    ]

    for idx, item in enumerate(recommendations[:10], start=1):
        story.append(Paragraph(f"{idx}. {item}", styles["BodyText"]))
        story.append(Spacer(1, 3))

    if not recommendations:
        story.append(Paragraph("No high-priority recommendations generated.", styles["BodyText"]))

    doc.build(story)
    return output_file
