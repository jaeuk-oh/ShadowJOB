"use client";

import { useMemo, useState } from "react";

function parseCsv(text: string): string[][] {
  const rows: string[][] = [];
  for (const line of text.trim().split(/\r?\n/)) {
    const cells: string[] = [];
    let cur = "";
    let inQ = false;
    for (let i = 0; i < line.length; i++) {
      const c = line[i];
      if (c === '"') inQ = !inQ;
      else if (c === "," && !inQ) {
        cells.push(cur);
        cur = "";
      } else cur += c;
    }
    cells.push(cur);
    rows.push(cells);
  }
  return rows;
}

export function AssetViewer({
  csv,
  dashboardMd,
}: {
  csv: string;
  dashboardMd: string;
}) {
  const [tab, setTab] = useState<"logs" | "dash">("logs");
  const rows = useMemo(() => parseCsv(csv), [csv]);
  const header = rows[0] ?? [];
  const body = rows.slice(1);

  return (
    <div className="col">
      <div className="col-head">
        자료
        <div className="tabs" style={{ marginLeft: "auto" }}>
          <span
            className={`tab ${tab === "logs" ? "active" : ""}`}
            onClick={() => setTab("logs")}
          >
            CS 로그 ({body.length})
          </span>
          <span
            className={`tab ${tab === "dash" ? "active" : ""}`}
            onClick={() => setTab("dash")}
          >
            대시보드
          </span>
        </div>
      </div>
      <div className="col-body">
        {tab === "logs" ? (
          <table>
            <thead>
              <tr>
                {header.map((h, i) => (
                  <th key={i}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {body.map((r, ri) => (
                <tr key={ri}>
                  {r.map((c, ci) => (
                    <td key={ci}>{c}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <pre className="dash">{dashboardMd}</pre>
        )}
      </div>
    </div>
  );
}
