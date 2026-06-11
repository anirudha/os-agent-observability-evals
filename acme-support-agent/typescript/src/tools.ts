/**
 * The three Acme tools, mirroring the Python version with the same fixed data
 * so evals are objective and the golden paths are identical across languages.
 */

const ORDERS: Record<string, unknown> = {
  "1007": { status: "shipped", items: ["Acme Rocket Skates"], ship_date: "2026-06-09" },
  "1042": { status: "processing", items: ["Acme Giant Rubber Band"], ship_date: null },
  "1099": { status: "delivered", items: ["Acme Anvil"], ship_date: "2026-06-01" },
};

const INVENTORY: Record<string, number> = {
  "SK-ROCKET": 14,
  "RB-GIANT": 0,
  "ANVIL-XL": 230,
};

const POLICY: Record<string, string> = {
  returns: "Items may be returned within 30 days of delivery for a full refund.",
  shipping: "Standard shipping is 3-5 business days. Express is next-day.",
  damaged: "Damaged items are replaced free of charge; contact support within 7 days.",
};

export function lookupOrder(orderId: string) {
  const id = String(orderId).trim().replace(/^#/, "");
  return ORDERS[id] ?? { error: "order_not_found", order_id: orderId };
}

export function checkInventory(sku: string) {
  const key = String(sku).trim().toUpperCase();
  const count = INVENTORY[key];
  return count !== undefined ? { sku, in_stock: count } : { error: "sku_not_found", sku };
}

export function searchPolicy(query: string) {
  const q = query.toLowerCase();
  for (const [topic, answer] of Object.entries(POLICY)) {
    if (q.includes(topic)) return { topic, answer };
  }
  return { topic: "returns", answer: POLICY.returns };
}

export const TOOL_FUNCTIONS: Record<string, (...args: any[]) => unknown> = {
  lookup_order: (a: { order_id: string }) => lookupOrder(a.order_id),
  check_inventory: (a: { sku: string }) => checkInventory(a.sku),
  search_policy: (a: { query: string }) => searchPolicy(a.query),
};

export const TOOL_SCHEMAS = [
  {
    name: "lookup_order",
    description: "Look up the status, items, and ship date of an order by its order ID.",
    parameters: {
      type: "object",
      properties: { order_id: { type: "string", description: "The order ID, e.g. 1007" } },
      required: ["order_id"],
    },
  },
  {
    name: "check_inventory",
    description: "Check how many units of a SKU are in stock.",
    parameters: {
      type: "object",
      properties: { sku: { type: "string", description: "The product SKU, e.g. SK-ROCKET" } },
      required: ["sku"],
    },
  },
  {
    name: "search_policy",
    description: "Search Acme's returns and shipping policy for an answer.",
    parameters: {
      type: "object",
      properties: { query: { type: "string", description: "What the customer is asking about" } },
      required: ["query"],
    },
  },
];

export const SYSTEM_PROMPT =
  "You are the Acme customer support agent. Use the provided tools to answer " +
  "customer questions about orders, inventory, and policies. Always call a tool " +
  "to get real data before answering — never guess. Keep answers short and friendly.";
