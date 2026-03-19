"""
Sentinel-NAC: PDF Report Generator
File: backend/reports/report_generator.py
Purpose: Generate a PDF audit report for a selected date range.

Dependencies: reportlab (pip install reportlab)
Output:       PDF file saved to REPORT_OUTPUT_DIR/
"""

import logging
import os
from datetime import datetime, date
from pathlib import Path
from typing import Optional, List, Dict

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import REPORT_OUTPUT_DIR
from database import db
from logs.logger import get_logger

logger = get_logger(__name__)

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph,
        Spacer, HRFlowable,
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning(
        "reportlab not installed. PDF generation unavailable. "
        "Run: pip install reportlab"
    )


# ---------------------------------------------------------------------------
# Data collection
# ---------------------------------------------------------------------------

def _collect_report_data(
    start_date: Optional[date] = None,
    end_date:   Optional[date] = None,
) -> Dict:
    """
    Query the database for report content.
    If dates are None, uses all-time data.
    """
    # Build date filters
    start_str = str(start_date) + " 00:00:00" if start_date else "1970-01-01 00:00:00"
    end_str   = str(end_date)   + " 23:59:59" if end_date   else "2099-12-31 23:59:59"

    # All devices seen in range
    devices = db.execute_query(
        """
        SELECT * FROM devices
         WHERE last_seen BETWEEN %s AND %s
         ORDER BY last_seen DESC
        """,
        (start_str, end_str),
        fetch=True,
    ) or []

    # Status counts
    status_counts = {"ALLOWED": 0, "BLOCKED": 0, "QUARANTINED": 0, "UNKNOWN": 0}
    for d in devices:
        s = d.get("status", "UNKNOWN")
        status_counts[s] = status_counts.get(s, 0) + 1

    # Top repeated unknown/quarantined devices
    top_restricted = db.execute_query(
        """
        SELECT d.mac_address, d.ip_address, d.vendor, d.status,
               COUNT(e.id) AS event_count
          FROM devices d
          LEFT JOIN device_events e ON d.mac_address = e.mac_address
         WHERE d.status IN ('QUARANTINED','BLOCKED','UNKNOWN')
           AND d.last_seen BETWEEN %s AND %s
         GROUP BY d.mac_address
         ORDER BY event_count DESC
         LIMIT 10
        """,
        (start_str, end_str),
        fetch=True,
    ) or []

    # Recent events timeline
    events = db.execute_query(
        """
        SELECT * FROM device_events
         WHERE created_at BETWEEN %s AND %s
         ORDER BY created_at DESC
         LIMIT 50
        """,
        (start_str, end_str),
        fetch=True,
    ) or []

    # Alert summary
    alerts = db.execute_query(
        """
        SELECT alert_type, status, COUNT(*) AS cnt
          FROM alerts
         WHERE created_at BETWEEN %s AND %s
         GROUP BY alert_type, status
        """,
        (start_str, end_str),
        fetch=True,
    ) or []

    return {
        "devices":       devices,
        "status_counts": status_counts,
        "top_restricted": top_restricted,
        "events":         events,
        "alerts":         alerts,
        "start_date":     start_str[:10],
        "end_date":       end_str[:10],
        "generated_at":   datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


# ---------------------------------------------------------------------------
# PDF builder
# ---------------------------------------------------------------------------

def _build_pdf(data: Dict, output_path: str) -> None:
    """Build and save the PDF report using reportlab."""
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm,   bottomMargin=2*cm,
    )
    styles  = getSampleStyleSheet()
    story   = []

    # -- Title --
    title_style = ParagraphStyle(
        "TitleStyle", parent=styles["Title"],
        fontSize=20, textColor=colors.HexColor("#1a1a2e"),
    )
    story.append(Paragraph("Sentinel-NAC Audit Report", title_style))
    story.append(Spacer(1, 0.3*cm))

    sub_style = ParagraphStyle(
        "SubStyle", parent=styles["Normal"],
        fontSize=10, textColor=colors.grey, alignment=TA_CENTER,
    )
    story.append(Paragraph(
        f"Period: {data['start_date']} to {data['end_date']}   |   "
        f"Generated: {data['generated_at']}",
        sub_style,
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    story.append(Spacer(1, 0.5*cm))

    h2 = ParagraphStyle("H2", parent=styles["Heading2"],
                         textColor=colors.HexColor("#16213e"))

    def section(title):
        story.append(Paragraph(title, h2))
        story.append(Spacer(1, 0.2*cm))

    # -- Summary --
    section("1. Summary")
    sc = data["status_counts"]
    total = sum(sc.values())
    summary_data = [
        ["Metric", "Count"],
        ["Total Devices Seen",   str(total)],
        ["ALLOWED",              str(sc.get("ALLOWED", 0))],
        ["QUARANTINED",          str(sc.get("QUARANTINED", 0))],
        ["BLOCKED",              str(sc.get("BLOCKED", 0))],
        ["UNKNOWN",              str(sc.get("UNKNOWN", 0))],
    ]
    story.append(_make_table(summary_data, col_widths=[10*cm, 5*cm]))
    story.append(Spacer(1, 0.5*cm))

    # -- Device List --
    section("2. Devices Detected")
    if data["devices"]:
        dev_data = [["MAC Address", "IP", "Vendor", "OS (est.)", "Status", "Last Seen"]]
        for d in data["devices"][:30]:  # cap at 30 rows
            dev_data.append([
                d.get("mac_address", ""),
                d.get("ip_address", ""),
                (d.get("vendor") or "")[:18],
                (d.get("probable_os") or "")[:15],
                d.get("status", ""),
                str(d.get("last_seen", ""))[:16],
            ])
        story.append(_make_table(
            dev_data,
            col_widths=[3.8*cm, 2.8*cm, 3.2*cm, 2.8*cm, 2.8*cm, 3.2*cm],
            highlight_col=4,  # highlight status column
        ))
    else:
        story.append(Paragraph("No devices found for this period.", styles["Normal"]))
    story.append(Spacer(1, 0.5*cm))

    # -- Top Restricted Devices --
    section("3. Top Restricted / Suspicious Devices")
    if data["top_restricted"]:
        top_data = [["MAC", "IP", "Vendor", "Status", "Event Count"]]
        for d in data["top_restricted"]:
            top_data.append([
                d.get("mac_address", ""),
                d.get("ip_address", ""),
                (d.get("vendor") or "")[:18],
                d.get("status", ""),
                str(d.get("event_count", 0)),
            ])
        story.append(_make_table(top_data))
    else:
        story.append(Paragraph("No restricted devices found.", styles["Normal"]))
    story.append(Spacer(1, 0.5*cm))

    # -- Events Timeline --
    section("4. Event Timeline (Last 50 Events)")
    if data["events"]:
        ev_data = [["Timestamp", "MAC", "Event Type", "Actor", "Details"]]
        for e in data["events"]:
            ev_data.append([
                str(e.get("created_at", ""))[:16],
                e.get("mac_address", ""),
                e.get("event_type", ""),
                e.get("actor", ""),
                (e.get("details") or "")[:30],
            ])
        story.append(_make_table(
            ev_data,
            col_widths=[3.5*cm, 3.5*cm, 3.8*cm, 2.5*cm, 4.9*cm],
        ))
    else:
        story.append(Paragraph("No events in this period.", styles["Normal"]))
    story.append(Spacer(1, 0.5*cm))

    # -- Footer note --
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "This report is generated by Sentinel-NAC for authorized lab use only. "
        "Handle with care — contains sensitive network device information.",
        ParagraphStyle("Footer", parent=styles["Normal"],
                       fontSize=8, textColor=colors.grey),
    ))

    doc.build(story)


def _make_table(
    data: List[List],
    col_widths=None,
    highlight_col: Optional[int] = None,
) -> "Table":
    """Build a styled reportlab Table from a list-of-lists."""
    STATUS_COLORS = {
        "ALLOWED":     colors.HexColor("#27ae60"),
        "BLOCKED":     colors.HexColor("#e74c3c"),
        "QUARANTINED": colors.HexColor("#e67e22"),
        "UNKNOWN":     colors.HexColor("#95a5a6"),
    }

    t = Table(data, colWidths=col_widths, repeatRows=1)
    base_style = [
        ("BACKGROUND",  (0, 0), (-1, 0),  colors.HexColor("#1a1a2e")),
        ("TEXTCOLOR",   (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",    (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, 0),  9),
        ("FONTSIZE",    (0, 1), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
        ("GRID",        (0, 0), (-1, -1), 0.3, colors.lightgrey),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",  (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]

    # Colour cells in the status column
    if highlight_col is not None:
        for row_idx in range(1, len(data)):
            cell_val = str(data[row_idx][highlight_col])
            if cell_val in STATUS_COLORS:
                base_style.append((
                    "TEXTCOLOR",
                    (highlight_col, row_idx),
                    (highlight_col, row_idx),
                    STATUS_COLORS[cell_val],
                ))
                base_style.append((
                    "FONTNAME",
                    (highlight_col, row_idx),
                    (highlight_col, row_idx),
                    "Helvetica-Bold",
                ))

    t.setStyle(TableStyle(base_style))
    return t


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def generate_report(
    start_date: Optional[date] = None,
    end_date:   Optional[date] = None,
    output_dir: str = REPORT_OUTPUT_DIR,
) -> str:
    """
    Generate a PDF report and return its file path.

    Args:
        start_date: Start of report period (date object or None for all time)
        end_date:   End of report period (date object or None for today)
        output_dir: Directory where the PDF will be saved

    Returns:
        Absolute path to the generated PDF file.

    Raises:
        RuntimeError if reportlab is not installed.
    """
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError(
            "reportlab is required for PDF generation. "
            "Install it with: pip install reportlab"
        )

    if end_date is None:
        end_date = date.today()

    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename   = f"sentinel_nac_report_{timestamp}.pdf"
    output_path = os.path.join(output_dir, filename)

    logger.info(
        "Generating report: start=%s end=%s output=%s",
        start_date, end_date, output_path,
    )

    data = _collect_report_data(start_date, end_date)
    _build_pdf(data, output_path)

    logger.info("Report generated: %s", output_path)
    return output_path


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Sentinel-NAC Report Generator")
    parser.add_argument("--start", help="Start date YYYY-MM-DD", default=None)
    parser.add_argument("--end",   help="End date YYYY-MM-DD",   default=None)
    parser.add_argument("--out",   help="Output directory",       default=REPORT_OUTPUT_DIR)
    args = parser.parse_args()

    start = date.fromisoformat(args.start) if args.start else None
    end   = date.fromisoformat(args.end)   if args.end   else None

    try:
        path = generate_report(start, end, args.out)
        print(f"Report saved: {path}")
    except RuntimeError as e:
        print(f"Error: {e}")
