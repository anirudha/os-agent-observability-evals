/**
 * The Acme agent — instrumented with the OpenSearch GenAI SDK for TypeScript.
 *
 * observe({ op: Op.INVOKE_AGENT }) wraps the whole turn as the root span; the
 * tools (wrapped in tools.ts) emit execute_tool spans; the chat call is wrapped
 * with observe({ op: Op.CHAT }) and enriched with token usage. This is the direct
 * TS equivalent of the Python register()+observe()+enrich() flow.
 */

import OpenAI from "openai";
import { observe, enrich, Op } from "@opensearch-project/genai-observability-sdk-ts";
import { TOOL_FUNCTIONS, TOOL_SCHEMAS, SYSTEM_PROMPT } from "./tools.js";

const MODEL = process.env.ACME_MODEL ?? "gpt-4o";

function openaiTools() {
  return TOOL_SCHEMAS.map((s) => ({ type: "function" as const, function: s }));
}

// One chat turn against the model, wrapped as a `chat` span with token usage.
const chatStep = observe(
  { name: "chat", op: Op.CHAT },
  async function chat(client: OpenAI, messages: any[]) {
    const resp = await client.chat.completions.create({
      model: MODEL,
      messages,
      tools: openaiTools(),
    });
    const usage = resp.usage;
    if (usage) {
      enrich({
        model: MODEL,
        provider: "openai",
        inputTokens: usage.prompt_tokens,
        outputTokens: usage.completion_tokens,
        totalTokens: usage.total_tokens,
      });
    }
    return resp.choices[0].message;
  },
);

export const handleSupportQuestion = observe(
  { name: "acme-support-agent", op: Op.INVOKE_AGENT },
  async function handleSupportQuestion(
    question: string,
    conversationId = "ts-session",
  ): Promise<string> {
    enrich({ model: MODEL, provider: "openai", sessionId: conversationId });

    const client = new OpenAI();
    const messages: any[] = [
      { role: "system", content: SYSTEM_PROMPT },
      { role: "user", content: question },
    ];

    for (let step = 0; step < 5; step++) {
      const msg = await chatStep(client, messages);

      if (!msg.tool_calls?.length) {
        return msg.content ?? "";
      }

      messages.push(msg);
      for (const call of msg.tool_calls) {
        const fn = TOOL_FUNCTIONS[call.function.name];
        const args = JSON.parse(call.function.arguments || "{}");
        const result = fn(args); // execute_tool span emitted by the wrapped tool
        messages.push({
          role: "tool",
          tool_call_id: call.id,
          content: JSON.stringify(result),
        });
      }
    }

    return "Sorry, I couldn't complete that request.";
  },
);
