"""
Sentinel-NAC: PDF Report Generator
File: backend/reports/report_generator.py
Purpose: Generates audit reports for network activity and device status.
"""

import os
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# Project modules
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from database import db

logger = logging.getLogger(__name__)

class ReportGenerator:
    def __init__(self, output_dir="reports/output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.styles = getSampleStyleSheet()

    def generate(self, start_date: str, end_date: str) -> str:
        """Generate a PDF report for the given date range."""
        filename = f"sentinel_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = self.output_dir / filename
        
        doc = SimpleDocTemplate(str(filepath), pagesize=letter)
        elements = []
        
        # Title
        elements.append(Paragraph("Sentinel-NAC: Network Audit Report", self.styles['Title']))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(f"Period: {start_date} to {end_date}", self.styles['Normal']))
        elements.append(Spacer(1, 24))
        
        # Summary Stats
        devices = db.get_all_devices()
        total = len(devices)
        allowed = len([d for d in devices if d['status'] == 'ALLOWED'])
        blocked = len([d for d in devices if d['status'] == 'BLOCKED'])
        quarantined = len([d for d in devices if d['status'] == 'QUARANTINED'])
        
        stats_data = [
            ["Metric", "Count"],
            ["Total Devices Discovered", total],
            ["Allowed Devices", allowed],
            ["Blocked Devices", blocked],
            ["Quarantined Devices", quarantined]
        ]
        
        t = Table(stats_data, colWidths=[200, 100])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ]))
        elements.append(Paragraph("System Summary", self.styles['Heading2']))
        elements.append(t)
        elements.append(Spacer(1, 24))
        
        # Device Table
        elements.append(Paragraph("Device Details", self.styles['Heading2']))
        device_data = [["MAC Address", "IP Address", "Vendor", "Status"]]
        for d in devices[:20]: # Limit to top 20 for report brevity
            device_data.append([
                d['mac_address'], 
                d['ip_address'], 
                (d['vendor'] or "Unknown")[:20], 
                d['status']
            ])
            
        t_dev = Table(device_data, colWidths=[120, 100, 150, 100])
        t_dev.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
        ]))
        elements.append(t_dev)
        
        doc.build(elements)
        logger.info("Report saved: %s", filepath)
        return str(filepath)

def main():
    parser = argparse.ArgumentParser(description="Sentinel-NAC Report Generator CLI")
    parser.add_argument("--start", help="Start date (YYYY-MM-DD)", default=(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"))
    parser.add_argument("--end", help="End date (YYYY-MM-DD)", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--out", help="Output directory", default="reports/output")
    args = parser.parse_args()
    
    gen = ReportGenerator(output_dir=args.out)
    path = gen.generate(args.start, args.end)
    print(f"Report saved: {path}")

if __name__ == "__main__":
    main()
