import fs from 'fs';
import path from 'path';
import matter from 'gray-matter';
import dotenv from 'dotenv';
import OpenAI from 'openai';

dotenv.config();

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

const INPUT_DIR = '../show-me-resistance/src/content/bill-breakdowns';
const files = fs.readdirSync(INPUT_DIR).filter((f) => f.endsWith('.md'));

for (const file of files) {
  const filePath = path.join(INPUT_DIR, file);
  const content = fs.readFileSync(filePath, 'utf8');
  const parsed = matter(content);

  const baseText = parsed.data.text || parsed.content;
  const limitedText = baseText.slice(0, 4000); // truncate for token safety

  const prompt = `
You are a civic analyst writing easy-to-understand, plain-English summaries of government legislation for public transparency.

BILL INFO:
Title: ${parsed.data.title}
Bill Number: ${parsed.data.bill_number}
Chamber: ${parsed.data.chamber}
Sponsor: ${parsed.data.sponsor}
Text: ${limitedText}

TASKS:
1. Write a one-sentence summary of this bill for a card-based UI that is easy to understand and thorough.
2. Write a multi-sentence plain-English explanation of what the bill does and who it affects.
3. Provide 3–6 useful tags that describe the bill's topic, impacted groups, policy type, or department.

If the bill text is limited, do your best to infer the meaning based on the title and description. Never leave any fields empty.

REPLY IN THIS YAML FORMAT:

summary_short: "..."
summary: |
  ...
tags:
  - ...
  - ...
`;

  try {
    const response = await openai.chat.completions.create({
      model: 'gpt-4.1-nano-2025-04-14',
      messages: [{ role: 'user', content: prompt }],
    });

    const yamlBlock = response.choices?.[0]?.message?.content;

    if (!yamlBlock) {
      console.warn(`❌ Empty response from GPT for ${file}`);
      fs.appendFileSync('gpt-errors.log', `\n\n### ${file}\n⚠️ Empty response`);
      continue;
    }

    // Try parsing the YAML block
    let gptParsed = {};
    try {
      gptParsed = matter(`${yamlBlock}\n${parsed.content}`).data;
    } catch (err) {
      console.error(`❌ YAML parse error in ${file}:`, err.message);
      fs.appendFileSync('gpt-errors.log', `\n\n### ${file}\n⚠️ YAML parse error:\n${yamlBlock}`);
      continue;
    }

    // Validate output quality
    const summaryShort = gptParsed.summary_short?.toLowerCase().trim();
    const title = parsed.data.title?.toLowerCase().trim();
    const tags = gptParsed.tags || [];

    const looksBad =
      !summaryShort ||
      summaryShort.length < 20 ||
      summaryShort === title ||
      tags.length < 2;

    if (looksBad) {
      console.warn(`⚠️ Skipping ${file} — summary looked lazy or incomplete`);
      fs.appendFileSync('gpt-errors.log', `\n\n### ${file}\n⚠️ Weak summary:\n${yamlBlock}`);
      continue;
    }

    // Merge frontmatter
    const merged = matter.stringify(parsed.content, {
      ...parsed.data,
      ...gptParsed,
    });

    fs.writeFileSync(filePath, merged, 'utf8');
    fs.appendFileSync('gpt-summary.log', `\n\n### ${file}\n${yamlBlock}`);
    console.log(`✅ Summarized ${file}`);
  } catch (err) {
    console.error(`❌ Error with ${file}:`, err.message);
    fs.appendFileSync('gpt-errors.log', `\n\n### ${file}\n❌ API Error: ${err.message}`);
  }
}
