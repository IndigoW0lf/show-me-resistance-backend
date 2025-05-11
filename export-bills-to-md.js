import fs from 'fs';
import path from 'path';
import mysql from 'mysql2/promise';

const OUTPUT_DIR = '../show-me-resistance/src/content/bill-breakdowns';

// Optional: create the folder if it doesn't exist
if (!fs.existsSync(OUTPUT_DIR)) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

// Map status_id values to readable labels
const STATUS_MAP = {
  1: 'Introduced',
  2: 'Engrossed',
  3: 'Enrolled',
  4: 'Passed',
  5: 'Vetoed',
  6: 'Failed',
  7: 'Enacted',
};

const db = await mysql.createConnection({
  host: 'localhost',
  user: 'legiscan_api',
  password: 'Goddess88!Goddess88!',
  database: 'legiscan_api',
});

const [bills] = await db.execute(`
  SELECT bill_id, bill_number, title, description, status_date, status_id
  FROM ls_bill
  WHERE date(status_date) >= '2024-01-01'
  ORDER BY status_date DESC
  LIMIT 50
`);

for (const bill of bills) {
  const slug = bill.bill_number.toLowerCase().replace(/[^a-z0-9]/g, '-');
  const fileName = `${slug}.md`;
  const filePath = path.resolve(OUTPUT_DIR, fileName);

  const status = STATUS_MAP[bill.status_id] || 'Unknown';
  const chamber = bill.bill_number?.startsWith('HB') || bill.bill_number?.startsWith('HR') || bill.bill_number?.startsWith('HCR')
    ? 'House'
    : 'Senate';

  const frontmatter = `---
title: "${bill.title?.replace(/"/g, "'") || 'Untitled'}"
bill_number: "${bill.bill_number}"
date: "${bill.status_date}"
status: "${status}"
chamber: "${chamber}"
draft: false
---
${bill.description || 'No description available.'}
`;

  fs.writeFileSync(filePath, frontmatter, 'utf8');
  console.log(`✅ Wrote ${fileName}`);
}

await db.end();
