/**
 * The Acme agent — manual gen_ai.* spans following the OTel GenAI semantic
 * conventions. Each LLM call becomes a `chat` span, each tool call an
 * `execute_tool` span, all under one `invoke_agent` root span.
 *
 * This is the manual equivalent of the Python SDK's register()+observe()+enrich().
 */

import { trace, context, SpanKind, SpanStatusCode } from "@opentelemetry/api";
import OpenAI from "openai";
import { TOOL_FUNCTIONS, TOOL_SCHEMAS, SYSTEM_PROMPT } from "./tools.js";

const tracer = trace.getTracer("acme-support-agent");
const MODEL = process.env.ACME_MODEL ?? "gpt-4o";

function openaiTools() {
  return TOOL_SCHEMAS.map((s) => ({ type: "function" as const, function: s }));
}

export async function handleSupportQuestion(
  question: string,
  conversationId = "ts-session",
): Promise<string> {
  return tracer.startActiveSpan(
    "invoke_agent",
    {
      kind: SpanKind.SERVER,
      attributes: {
        "gen_ai.operation.name": "invoke_agent",
        "gen_ai.agent.name": "acme-support-agent",
        "gen_ai.request.model": MODEL,
        "gen_ai.conversation.id": conversationId,
      },
    },
    async (agentSpan) => {
      try {
        const client = new OpenAI();
        const messages: any[] = [
          { role: "system", content: SYSTEM_PROMPT },
          { role: "user", content: question },
        ];

        for (let step = 0; step < 5; step++) {
          // ---- chat span ----
          const msg = await tracer.startActiveSpan(
            "chat",
            { attributes: { "gen_ai.operation.name": "chat", "gen_ai.request.model": MODEL } },
            async (chatSpan) => {
              const resp = await client.chat.completions.create({
                model: MODEL,
                messages,
                tools: openaiTools(),
              });
              const usage = resp.usage;
              if (usage) {
                chatSpan.setAttribute("gen_ai.usage.input_tokens", usage.prompt_tokens);
                chatSpan.setAttribute("gen_ai.usage.output_tokens", usage.completion_tokens);
              }
              chatSpan.end();
              return resp.choices[0].message;
            },
          );

          if (!msg.tool_calls?.length) {
            agentSpan.end();
            return msg.content ?? "";
          }

          messages.push(msg);
          for (const call of msg.tool_calls) {
            // ---- execute_tool span ----
            const result = await tracer.startActiveSpan(
              "execute_tool",
              {
                attributes: {
                  "gen_ai.operation.name": "execute_tool",
                  "gen_ai.tool.name": call.function.name,
                  "gen_ai.tool.call.id": call.id,
                  "gen_ai.tool.call.arguments": call.function.arguments,
                },
              },
              (toolSpan) => {
                const fn = TOOL_FUNCTIONS[call.function.name];
                const args = JSON.parse(call.function.arguments || "{}");
                const r = fn(args);
                toolSpan.setAttribute("gen_ai.tool.call.result", JSON.stringify(r));
                toolSpan.end();
                return r;
              },
            );
            messages.push({
              role: "tool",
              tool_call_id: call.id,
              content: JSON.stringify(result),
            });
          }
        }

        agentSpan.end();
        return "Sorry, I couldn't complete that request.";
      } catch (err) {
        agentSpan.setStatus({ code: SpanStatusCode.ERROR, message: String(err) });
        agentSpan.recordException(err as Error);
        agentSpan.end();
        throw err;
      }
    },
  );
}
