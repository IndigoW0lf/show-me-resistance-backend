/**
 * export_bill_metadata.js
 *
 * DESCRIPTION:
 * This script exports metadata for Missouri bills (2024 session and beyond) from your
 * local MySQL `legiscan_api` database and writes them to Markdown files for use in
 * the Show Me Resistance Astro frontend (`src/content/bill-breakdowns/`).
 *
 * It performs the following steps:
 *
 * 1. Connects to the `legiscan_api` database.
 * 2. Retrieves all bills from 2024 onward, ordered by `status_date` (most recent first).
 * 3. Converts each bill into a Markdown file:
 *    - Includes YAML frontmatter: `title`, `bill_number`, `date`, `status`, `chamber`, etc.
 *    - Inserts description and a link to the full LegiScan-hosted bill text.
 * 4. Uses `change_hash` to skip unchanged bills for incremental updates.
 * 5. Tracks hashes in `bill-index.json` to prevent redundant processing.
 *
 * OUTPUT:
 * - Markdown files: One per bill (e.g., `hb1594.md`)
 * - `bill-index.json`: Maps `bill_number` to `change_hash` for future diffs
 *
 * USAGE:
 * Run this to sync new or updated bill metadata to the Astro frontend.
 * It does NOT include `full_text` (PDF contents) or GPT-generated summaries.
 *
 * PIPELINE CONTEXT:
 * - 📤 This is usually the **first** export step to refresh metadata for the site.
 * - 🧹 Optional: Use `clean-bill-frontmatter.js` beforehand to wipe old YAML blocks.
 * - 🔗 Run BEFORE `extract_bill_text_dir.py` (to decode PDFs) and `summarize_and_save.py` (to generate GPT summaries).
 * - 🧠 This step enables the frontend to render cards with basic metadata (status, title, sponsor, etc.).
 *
 * REQUIREMENTS:
 * - Node.js environment with `mysql2`, `fs`
 * - Valid MySQL schema with `ls_bill` and `ls_bill_text` tables
 *
 * TIP:
 * Use with `backfill_full_text.py` and `summarize_and_save.py` for a full end-to-end sync.
 *
 * Author: Kai Wolf
 * Last updated: 2025-05-11
 */

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

// Get basic bill data and text
const [bills] = await db.execute(`
  SELECT b.bill_id, b.bill_number, b.title, b.description, b.status_date,
         b.status_id, b.change_hash,
         bt.legiscan_url
  FROM ls_bill b
  LEFT JOIN ls_bill_text bt ON bt.bill_id = b.bill_id
  WHERE date(b.status_date) >= '2024-01-01'
  ORDER BY b.status_date DESC
`);

for (const bill of bills) {
    const hash = bill.change_hash;
    const billNumber = bill.bill_number;
    const slug = billNumber.toLowerCase().replace(/[^a-z0-9]/g, '-');
    const fileName = `${slug}.md`;
    const filePath = path.resolve(OUTPUT_DIR, fileName);

    if (billIndex[billNumber] === hash) {
        console.log(`⏩ Skipping unchanged ${billNumber}`);
        continue;
    }

    const status = STATUS_MAP[bill.status_id] || 'Unknown';
    const chamber = /^H(B|R|CR)/.test(billNumber) ? 'House' : 'Senate';

    const frontmatter = `---
title: "${bill.title?.replace(/"/g, "'") || 'Untitled'}"
bill_number: "${billNumber}"
date: "${bill.status_date}"
status: "${status}"
chamber: "${chamber}"
sponsor: "Unknown"
vote_summary: "Unavailable"
legiscan_url: "${bill.legiscan_url || ''}"
draft: false
---

${bill.description || 'No description available.'}

---

## Read Full Bill Text

You can view the full text [here](${bill.legiscan_url || 'https://legiscan.com'}).
`;

    fs.writeFileSync(filePath, frontmatter, 'utf8');
    console.log(`✅ Wrote ${fileName}`);
    billIndex[billNumber] = hash;
}

fs.writeFileSync(INDEX_FILE, JSON.stringify(billIndex, null, 2), 'utf8');
console.log('🧾 bill-index.json updated.');

await db.end();
