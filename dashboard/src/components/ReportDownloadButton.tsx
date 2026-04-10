"use client";

import { jsPDF } from "jspdf";
import autoTable from "jspdf-autotable";
import { Download, FileText } from "lucide-react";
import { format } from "date-fns";

interface ReportDownloadButtonProps {
  data: any[];
  title: string;
  filename: string;
}

export default function ReportDownloadButton({ data, title, filename }: ReportDownloadButtonProps) {
  const downloadPDF = () => {
    const doc = new jsPDF();
    
    // Add title
    doc.setFontSize(20);
    doc.setTextColor(40);
    doc.text("SENTINEL-NAC SYSTEM REPORT", 14, 22);
    
    doc.setFontSize(14);
    doc.text(title.toUpperCase(), 14, 32);
    
    doc.setFontSize(10);
    doc.setTextColor(100);
    doc.text(`Generated: ${format(new Date(), "yyyy-MM-dd HH:mm:ss")}`, 14, 40);
    
    // Add Table
    const tableData = data.map(event => [
      event.eventType,
      event.macAddress,
      event.details || "N/A",
      event.actor || "SYSTEM",
      format(new Date(event.createdAt), "yyyy-MM-dd HH:mm:ss")
    ]);
    
    autoTable(doc, {
      startY: 50,
      head: [["EVENT_TYPE", "NODE_ID", "DETAILS", "ACTOR", "TIMESTAMP"]],
      body: tableData,
      theme: "striped",
      headStyles: { fillColor: [34, 197, 94] }, // Technical Green
      styles: { font: "courier", fontSize: 8 },
    });
    
    doc.save(`${filename}_${format(new Date(), "yyyyMMdd_HHmmss")}.pdf`);
  };

  return (
    <button 
      onClick={downloadPDF}
      className="flex items-center gap-2 px-6 py-2.5 text-[10px] font-black uppercase tracking-[0.2em] bg-accent text-black hover:bg-white transition-colors"
    >
      <Download className="w-3.5 h-3.5" />
      Download_PDF_Report
    </button>
  );
}
