"use client";

interface TranscriptSegment {
  speaker?: string;
  text?: string;
  start: number;
  end: number;
}

export interface TranscriptData {
  segments?: TranscriptSegment[];
}

export interface PrintCallRecord {
  transcriptFilename: string;
  gradeFilename?: string;
  audioFilename?: string;
  dispatcherName: string;
  dateTime: Date;
  nature: string;
  gradePercentage: number;
  detectedNatureCode?: string;
  questionGrades: Record<
    string,
    { label: string; status: string; reasoning?: string }
  >;
  transcriptData: TranscriptData | null;
}

const formatTime = (seconds: number): string => {
  const m = Math.floor(seconds / 60)
    .toString()
    .padStart(2, "0");
  const s = Math.floor(seconds % 60)
    .toString()
    .padStart(2, "0");
  return `${m}:${s}`;
};

const getStatusColor = (status: string): string => {
  const s = status.trim().toLowerCase();
  if (s === "asked correctly" || s === "obvious") return "#16a34a";
  if (s === "not asked" || s === "asked incorrectly") return "#dc2626";
  if (s === "not as scripted") return "#d97706";
  return "#6b7280";
};

const getGradeColor = (pct: number): string => {
  if (pct >= 80) return "#16a34a";
  if (pct >= 50) return "#d97706";
  return "#dc2626";
};

const escapeHtml = (value: unknown): string =>
  String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");

const formatMultilineHtml = (value?: string): string => {
  if (!value) {
    return "";
  }

  return escapeHtml(value).replace(/\r?\n/g, "<br />");
};

const normalizeDisplayValue = (value: unknown): string => {
  if (typeof value === "string" || typeof value === "number") {
    return String(value);
  }

  if (value && typeof value === "object") {
    const maybeRecord = value as Record<string, unknown>;
    const codeValue =
      typeof maybeRecord.id === "string" || typeof maybeRecord.id === "number"
        ? String(maybeRecord.id)
        : typeof maybeRecord.code === "string" ||
            typeof maybeRecord.code === "number"
          ? String(maybeRecord.code)
          : "";
    const nameValue =
      typeof maybeRecord.name === "string" ||
      typeof maybeRecord.name === "number"
        ? String(maybeRecord.name)
        : "";

    if (codeValue && nameValue) {
      return `${codeValue}: ${nameValue}`;
    }

    if (codeValue) {
      return codeValue;
    }

    if (nameValue) {
      return nameValue;
    }
  }

  return "";
};

const buildHtml = (records: PrintCallRecord[]): string => {
  const callSections = records
    .map((record, index) => {
      const segments = record.transcriptData?.segments ?? [];

      const questionRows = Object.entries(record.questionGrades)
        .map(([, q], rowIdx) => {
          const reasoningText = formatMultilineHtml(q.reasoning);
          const reasoningBlock = reasoningText
            ? `<div style="font-size:12px;font-weight:500;color:#4b5563;margin-top:6px;line-height:1.65">${reasoningText}</div>`
            : `<div style="font-size:12px;color:#9ca3af;font-style:italic;margin-top:6px;line-height:1.5">No reasoning provided.</div>`;

          return `
        <tr style="background:${rowIdx % 2 === 0 ? "#fff" : "#f8fafc"}">
          <td style="padding:9px 10px;border-bottom:1px solid #f1f5f9;color:#374151;font-size:13px">
            <div style="font-size:13px;font-weight:700;color:#1f2937;line-height:1.45">${escapeHtml(q.label)}</div>
            ${reasoningBlock}
          </td>
          <td style="padding:9px 10px;border-bottom:1px solid #f1f5f9;text-align:right;font-size:13px;font-weight:700;color:${getStatusColor(q.status)};vertical-align:top;white-space:nowrap;width:1%">${escapeHtml(q.status)}</td>
        </tr>
      `;
        })
        .join("");

      const transcriptLines = segments
        .map((seg) => {
          const isDispatcher = seg.speaker !== "caller";

          return `
        <div style="display:flex;gap:12px;align-items:flex-start;margin-bottom:10px">
          <span style="font-size:10px;color:#9ca3af;font-family:monospace;min-width:42px;padding-top:2px;flex-shrink:0">${formatTime(seg.start)}</span>
          <div style="max-width:85%;${isDispatcher ? "" : "margin-left:auto"};flex:1">
            <div style="font-size:10px;font-weight:700;margin-bottom:3px;color:${isDispatcher ? "#1e3a5f" : "#065f46"};text-transform:uppercase;letter-spacing:0.06em">${escapeHtml(seg.speaker || "unknown")}</div>
            <div style="padding:8px 12px;border-radius:8px;font-size:13px;line-height:1.5;background:${isDispatcher ? "#eff6ff" : "#f0fdf4"};border:1px solid ${isDispatcher ? "#bfdbfe" : "#bbf7d0"};color:#1a1a1a">${formatMultilineHtml(seg.text || "")}</div>
          </div>
        </div>
      `;
        })
        .join("");

      const pageBreak =
        index < records.length - 1 ? 'style="page-break-after:always"' : "";

      return `
      <div ${pageBreak}>
        <div style="border-bottom:3px solid #1e3a5f;padding-bottom:16px;margin-bottom:28px;display:flex;justify-content:space-between;align-items:flex-start">
          <div>
            <p style="font-size:11px;letter-spacing:0.12em;text-transform:uppercase;color:#6b7280;margin:0 0 4px 0">Emergency Medical Call Analysis</p>
            <h1 style="font-size:26px;font-weight:700;color:#1e3a5f;margin:0">Dispatcher Call Record</h1>
          </div>
          ${records.length > 1 ? `<div style="font-size:12px;color:#6b7280;margin-top:8px">Call ${index + 1} of ${records.length}</div>` : ""}
        </div>

        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px 32px;margin-bottom:28px;padding:20px 24px;background:#f8fafc;border-radius:6px;border:1px solid #e2e8f0">
          <div>
            <div style="font-size:10px;text-transform:uppercase;letter-spacing:0.08em;color:#9ca3af;margin-bottom:2px">Dispatcher</div>
            <div style="font-size:14px;font-weight:600">${escapeHtml(record.dispatcherName)}</div>
          </div>
          <div>
            <div style="font-size:10px;text-transform:uppercase;letter-spacing:0.08em;color:#9ca3af;margin-bottom:2px">Grade</div>
            <div style="font-size:18px;font-weight:700;color:${getGradeColor(record.gradePercentage)}">${record.gradePercentage.toFixed(1)}%</div>
          </div>
          <div>
            <div style="font-size:10px;text-transform:uppercase;letter-spacing:0.08em;color:#9ca3af;margin-bottom:2px">Date</div>
            <div style="font-size:14px;font-weight:600">${record.dateTime.toLocaleDateString("en-US", { weekday: "long", year: "numeric", month: "long", day: "numeric" })}</div>
          </div>
          <div>
            <div style="font-size:10px;text-transform:uppercase;letter-spacing:0.08em;color:#9ca3af;margin-bottom:2px">Time</div>
            <div style="font-size:14px;font-weight:600">${record.dateTime.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", second: "2-digit" })}</div>
          </div>
          <div>
            <div style="font-size:10px;text-transform:uppercase;letter-spacing:0.08em;color:#9ca3af;margin-bottom:2px">Nature Code</div>
            <div style="font-size:14px;font-weight:600">${escapeHtml(normalizeDisplayValue(record.detectedNatureCode) || "-")}</div>
          </div>
          <div style="grid-column:1/-1">
            <div style="font-size:10px;text-transform:uppercase;letter-spacing:0.08em;color:#9ca3af;margin-bottom:2px">Files</div>
            <div style="font-size:11px;font-weight:600;font-family:monospace;color:#6b7280">${escapeHtml(record.transcriptFilename)}</div>
            <div style="font-size:11px;font-weight:600;font-family:monospace;color:#6b7280">${escapeHtml(record.gradeFilename || "-")}</div>
            <div style="font-size:11px;font-weight:600;font-family:monospace;color:#6b7280">${escapeHtml(record.audioFilename || "-")}</div>
          </div>
        </div>

        <div style="margin-bottom:28px">
          <h2 style="font-size:14px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:#1e3a5f;border-bottom:1px solid #e2e8f0;padding-bottom:8px;margin-bottom:12px">Grading Results</h2>
          ${Object.keys(record.questionGrades).length === 0
            ? `<p style="color:#9ca3af;font-style:italic">No grading data available.</p>`
            : `<table style="width:100%;border-collapse:collapse">
                <thead>
                  <tr style="background:#f1f5f9">
                    <th style="text-align:left;padding:8px 10px;font-weight:600;color:#374151;border-bottom:1px solid #e2e8f0;font-size:13px">Question</th>
                    <th style="text-align:right;padding:8px 10px;font-weight:600;color:#374151;border-bottom:1px solid #e2e8f0;white-space:nowrap;font-size:13px">Result</th>
                  </tr>
                </thead>
                <tbody>${questionRows}</tbody>
              </table>`
          }
        </div>

        <div>
          <h2 style="font-size:14px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:#1e3a5f;border-bottom:1px solid #e2e8f0;padding-bottom:8px;margin-bottom:16px">Full Transcript</h2>
          ${segments.length === 0
            ? `<p style="color:#9ca3af;font-style:italic">No transcript available.</p>`
            : transcriptLines}
        </div>

        <div style="margin-top:40px;padding-top:12px;border-top:1px solid #e2e8f0;display:flex;justify-content:space-between;font-size:10px;color:#9ca3af">
          <span>Emergency Medical Call Analysis System</span>
          <span>Exported ${new Date().toLocaleString()}</span>
        </div>
      </div>
    `;
    })
    .join("");

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Dispatcher Call Record - ${escapeHtml(records[0]?.dispatcherName ?? "")}</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: #1a1a1a;
      background: #f3f4f6;
      padding: 32px 16px;
    }
    .page {
      background: #fff;
      max-width: 800px;
      margin: 0 auto;
      padding: 40px 48px;
      border-radius: 6px;
      box-shadow: 0 2px 12px rgba(0,0,0,0.08);
    }
    .toolbar {
      max-width: 800px;
      margin: 0 auto 20px;
      display: flex;
      gap: 10px;
      align-items: center;
    }
    .btn-print {
      background: #1e3a5f;
      color: #fff;
      border: none;
      border-radius: 6px;
      padding: 9px 20px;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
    }
    .btn-close {
      background: #f1f5f9;
      color: #374151;
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      padding: 9px 16px;
      font-size: 14px;
      cursor: pointer;
    }
    @media print {
      body { background: #fff; padding: 0; }
      .toolbar { display: none; }
      .page { box-shadow: none; border-radius: 0; padding: 24px 32px; }
    }
  </style>
</head>
<body>
  <div class="toolbar">
    <strong style="color:#1e3a5f;font-size:14px">
      ${records.length === 1 ? "1 call record" : `${records.length} call records`} - ${escapeHtml(records[0]?.dispatcherName ?? "")}
    </strong>
    <button class="btn-print" onclick="window.print()">Print / Save as PDF</button>
    <button class="btn-close" onclick="window.close()">Close</button>
  </div>
  <div class="page">
    ${callSections}
  </div>
</body>
</html>`;
};

export const exportRecord = (records: PrintCallRecord[]): void => {
  const html = buildHtml(records);
  const blob = new Blob([html], { type: "text/html" });
  const url = URL.createObjectURL(blob);
  const tab = window.open(url, "_blank");
  if (tab) {
    tab.addEventListener("load", () => URL.revokeObjectURL(url), {
      once: true,
    });
  }
};

export default exportRecord;
