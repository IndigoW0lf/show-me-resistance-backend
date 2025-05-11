import fs from 'fs';
import path from 'path';
import mysql from 'mysql2/promise';

const OUTPUT_DIR = '../show-me-resistance/src/content/bill-breakdowns';
const INDEX_FILE = './bill-index.json';

// Create content dir if missing
if (!fs.existsSync(OUTPUT_DIR)) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

// Load or initialize bill index
let billIndex = {};
if (fs.existsSync(INDEX_FILE)) {
  billIndex = JSON.parse(fs.readFileSync(INDEX_FILE, 'utf8'));
}

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

// Get recent bills + change_hash
const [bills] = await db.execute(`
  SELECT b.bill_id, b.bill_number, b.title, b.description, b.status_date,
         b.status_id, b.change_hash,
         bt.legiscan_url,
         p.full_name AS sponsor_name, p.party, p.district,
         rc.yea, rc.nay, rc.absent, rc.roll_call_date
  FROM ls_bill b
  LEFT JOIN ls_bill_text bt ON bt.bill_id = b.bill_id
  LEFT JOIN ls_sponsor s ON s.bill_id = b.bill_id
  LEFT JOIN ls_person p ON s.person_id = p.person_id
  LEFT JOIN ls_roll_call rc ON rc.bill_id = b.bill_id
  WHERE date(b.status_date) >= '2024-01-01'
  ORDER BY b.status_date DESC
`);

for (const bill of bills) {
  const hash = bill.change_hash;
  const billNumber = bill.bill_number;
  const slug = billNumber.toLowerCase().replace(/[^a-z0-9]/g, '-');
  const fileName = `${slug}.md`;
  const filePath = path.resolve(OUTPUT_DIR, fileName);

  // Skip if unchanged
  if (billIndex[billNumber] === hash) {
    console.log(`⏩ Skipping unchanged ${billNumber}`);
    continue;
  }

  const status = STATUS_MAP[bill.status_id] || 'Unknown';
  const chamber =
    billNumber.startsWith('HB') || billNumber.startsWith('HR') || billNumber.startsWith('HCR')
      ? 'House'
      : 'Senate';

  const sponsor =
    bill.sponsor_name
      ? `${bill.sponsor_name} (${bill.party || '?'} - ${bill.district || 'Unknown'})`
      : 'Unknown';

  const voteSummary = bill.roll_call_date
    ? `Passed ${bill.yea || 0}–${bill.nay || 0} on ${new Date(bill.roll_call_date).toLocaleDateString()}`
    : 'No roll call vote data available.';

  const billTextUrl = bill.legiscan_url || 'Not    available';


  const frontmatter = `---
title: "${bill.title?.replace(/"/g, "'") || 'Untitled'}"
bill_number: "${billNumber}"
date: "${bill.status_date}"
status: "${status}"
chamber: "${chamber}"
sponsor: "${sponsor}"
vote_summary: "${voteSummary}"
draft: false
---

${bill.description || 'No description available.'}

---

---

## Read Full Bill Text

You can view the full text [here](${billTextUrl}).

`;

  fs.writeFileSync(filePath, frontmatter, 'utf8');
  console.log(`✅ Wrote ${fileName}`);

  // Update index
  billIndex[billNumber] = hash;
}

// Save updated index
fs.writeFileSync(INDEX_FILE, JSON.stringify(billIndex, null, 2), 'utf8');
console.log('🧾 bill-index.json updated.');

await db.end();
