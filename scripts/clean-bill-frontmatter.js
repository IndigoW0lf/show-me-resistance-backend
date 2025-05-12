/**
 * clean-bill-frontmatter.js
 *
 * DESCRIPTION:
 * This script removes all metadata fields (frontmatter) from Markdown files
 * in the `bill-breakdowns` content directory of the Show Me Resistance site.
 *
 * It performs the following:
 *
 * 1. Loads all `.md` files from the specified directory.
 * 2. Parses the frontmatter using `gray-matter`.
 * 3. Deletes known fields such as:
 *    - title, bill_number, status, sponsor, summary, tags, etc.
 * 4. Writes the cleaned content back to disk with only body text remaining.
 *
 * USE CASE:
 * - Useful when resetting scraped or AI-generated bill content for reprocessing.
 * - Prevents duplicate or outdated summaries or metadata from being preserved in markdown.
 *
 * PIPELINE CONTEXT:
 * - 🧼 Run this **before** re-importing fresh metadata from the SQL database
 *   (e.g., using `export_bills_to_md.js`) to avoid conflicts or duplication.
 * - 📦 Typically used when migrating from local `.md` workflows to a DB-backed frontend.
 * - 🔁 Can be safely run multiple times.
 * - ❌ Do not run this if you want to preserve AI summaries or YAML fields already edited.
 *
 * WARNING:
 * This permanently removes YAML fields from all Markdown files in the directory.
 * Only use this script when you're sure you want to wipe all metadata.
 *
 * REQUIREMENTS:
 * - Node.js environment with `gray-matter` installed
 *
 * USAGE:
 * Run with: `node scripts/clean-bill-frontmatter.js`
 *
 * Author: Kai Wolf
 * Last updated: 2025-05-11
 */

// scripts/clean-bill-frontmatter.js
import fs from 'fs';
import path from 'path';
import matter from 'gray-matter';

const INPUT_DIR = '../show-me-resistance/src/content/bill-breakdowns';
const files = fs.readdirSync(INPUT_DIR).filter((f) => f.endsWith('.md'));

// List of fields to wipe from frontmatter
const FIELDS_TO_DELETE = [
    'title',
    'bill_number',
    'date',
    'status',
    'chamber',
    'sponsor',
    'vote_summary',
    'legiscan_url',
    'draft',
    'summary_short',
    'summary',
    'tags',
    'bill_text',
];

for (const file of files) {
    const filePath = path.join(INPUT_DIR, file);
    const content = fs.readFileSync(filePath, 'utf8');
    const parsed = matter(content);

    FIELDS_TO_DELETE.forEach((field) => delete parsed.data[field]);

    const cleaned = matter.stringify(parsed.content.trim(), parsed.data);
    fs.writeFileSync(filePath, cleaned);
    console.log(`🧹 Cleared frontmatter in ${file}`);
}
