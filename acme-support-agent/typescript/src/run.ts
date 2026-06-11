/**
 * CLI runner. Import observability.ts FIRST so OTel starts before the agent.
 *
 *   npm run dev -- "where is my order #1007?"
 *   npm run build && npm start -- "is SK-ROCKET in stock?"
 */

import "./observability.js";
import { handleSupportQuestion } from "./agent.js";

const question = process.argv.slice(2).join(" ") || "where is my order #1007?";

handleSupportQuestion(question)
  .then((answer) => {
    console.log(`\n🤖 ${answer}\n`);
    // give the exporter a moment to flush before exit
    setTimeout(() => process.exit(0), 2000);
  })
  .catch((err) => {
    console.error(err);
    process.exit(1);
  });
