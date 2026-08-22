"use strict";

const fs = require("fs");
const {
  AlignmentType,
  BorderStyle,
  Document,
  Footer,
  HeadingLevel,
  Packer,
  PageNumber,
  Paragraph,
  ShadingType,
  Table,
  TableCell,
  TableRow,
  TextRun,
  WidthType,
} = require("docx");

const TABLE_WIDTH = 9638;
const border = { style: BorderStyle.SINGLE, size: 1, color: "B7C9D6" };
const borders = { top: border, bottom: border, left: border, right: border };

function text(value) {
  return value === null || value === undefined ? "" : String(value);
}

function cell(value, width, header = false) {
  return new TableCell({
    borders,
    width: { size: width, type: WidthType.DXA },
    shading: header ? { fill: "D9EAF7", type: ShadingType.CLEAR } : undefined,
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    children: [
      new Paragraph({
        children: [new TextRun({ text: text(value), bold: header, font: "Arial" })],
      }),
    ],
  });
}

function table(headers, rows, widths) {
  return new Table({
    width: { size: TABLE_WIDTH, type: WidthType.DXA },
    columnWidths: widths,
    rows: [
      new TableRow({ children: headers.map((value, index) => cell(value, widths[index], true)) }),
      ...rows.map(
        (row) => new TableRow({ children: row.map((value, index) => cell(value, widths[index])) }),
      ),
    ],
  });
}

function labeled(label, value) {
  return new Paragraph({
    spacing: { after: 80 },
    children: [
      new TextRun({ text: `${label}: `, bold: true, font: "Arial" }),
      new TextRun({ text: text(value), font: "Arial" }),
    ],
  });
}

async function main() {
  const report = JSON.parse(fs.readFileSync(0, "utf8"));
  const children = [
    new Paragraph({
      heading: HeadingLevel.HEADING_1,
      alignment: AlignmentType.CENTER,
      children: [new TextRun("Security Report")],
    }),
    labeled("Generated", report.generated_at),
    new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("Scan Sources")] }),
    table(
      ["Tool", "Version", "Ruleset", "Target", "Started At"],
      report.sources.map((source) => [
        source.tool,
        source.tool_version,
        source.ruleset,
        source.target,
        source.started_at,
      ]),
      [1300, 1300, 2200, 2638, 2200],
    ),
    new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("Summary")] }),
    table(
      ["Severity", "Count"],
      [
        ["Total", report.summary.total],
        ["Error", report.summary.error],
        ["Warning", report.summary.warning],
        ["Info", report.summary.info],
        ["Unknown", report.summary.unknown],
      ],
      [4819, 4819],
    ),
    new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("Findings")] }),
  ];

  if (report.findings.length === 0) {
    children.push(new Paragraph("No findings."));
  }
  for (const finding of report.findings) {
    children.push(
      new Paragraph({
        heading: HeadingLevel.HEADING_3,
        children: [new TextRun(`[${finding.severity}] ${finding.rule_id}`)],
      }),
      labeled("Tool", finding.tool),
      labeled("Location", `${finding.path}:${finding.start_line}`),
      labeled("ID", finding.id),
      labeled("Message", finding.message),
      labeled("Raw reference", finding.raw_reference),
    );
    if (finding.code) {
      children.push(labeled("Code", finding.code));
    }
    if (finding.metadata && Object.keys(finding.metadata).length > 0) {
      children.push(labeled("Metadata", JSON.stringify(finding.metadata)));
    }
  }

  const document = new Document({
    styles: {
      default: { document: { run: { font: "Arial", size: 20 } } },
      paragraphStyles: [
        {
          id: "Heading1",
          name: "Heading 1",
          basedOn: "Normal",
          next: "Normal",
          quickFormat: true,
          run: { font: "Arial", size: 32, bold: true },
          paragraph: { spacing: { before: 240, after: 240 }, outlineLevel: 0 },
        },
        {
          id: "Heading2",
          name: "Heading 2",
          basedOn: "Normal",
          next: "Normal",
          quickFormat: true,
          run: { font: "Arial", size: 28, bold: true },
          paragraph: { spacing: { before: 220, after: 140 }, outlineLevel: 1 },
        },
        {
          id: "Heading3",
          name: "Heading 3",
          basedOn: "Normal",
          next: "Normal",
          quickFormat: true,
          run: { font: "Arial", size: 24, bold: true },
          paragraph: { spacing: { before: 180, after: 100 }, outlineLevel: 2 },
        },
      ],
    },
    sections: [
      {
        properties: {
          page: {
            size: { width: 11906, height: 16838 },
            margin: { top: 1134, right: 1134, bottom: 1134, left: 1134 },
          },
        },
        footers: {
          default: new Footer({
            children: [
              new Paragraph({
                alignment: AlignmentType.CENTER,
                children: [new TextRun("Page "), new TextRun({ children: [PageNumber.CURRENT] })],
              }),
            ],
          }),
        },
        children,
      },
    ],
  });
  process.stdout.write(await Packer.toBuffer(document));
}

main().catch((error) => {
  process.stderr.write(error instanceof Error ? error.message : "DOCX rendering failed");
  process.exitCode = 1;
});
