import os, anthropic
from datetime import date, timedelta
from tavily import TavilyClient

client = anthropic.Anthropic()
tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

tools = [{
    "name": "web_search",
    "description": "Search the web for current sports stats, odds, and betting trends.",
    "input_schema": {
        "type": "object",
        "properties": {"query": {"type": "string", "description": "Search query"}},
        "required": ["query"]
    }
}]

def run_search(query):
    results = tavily.search(query=query, max_results=3)
    return "\n".join(f"- {r['title']}: {r['content'][:120]}" for r in results["results"])

tomorrow = (date.today() + timedelta(days=1)).strftime("%B %d, %Y")
question = f"Tomorrow is {tomorrow}. What are the best specific player prop and team picks to bet on for {tomorrow}? Search for {tomorrow} games, player prop lines, and recent stats. Give me concrete actionable picks like 'Luka Doncic over 3.5 assists' with a reason why based on stats."
print(f"\n🙋 Getting picks for {tomorrow}...\n")

system = "You are a sharp sports betting analyst. When you have enough data, give 3-5 concrete, specific picks in this format: 🏀/🏒/⚾ [Player/Team] — [Bet type & line] — [Reason based on stats]. Be direct and specific, no generic advice."

messages = [{"role": "user", "content": question}]

while True:
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=system,
        tools=tools,
        messages=messages
    )

    tool_results = []
    for block in response.content:
        if block.type == "tool_use":
            print(f"🔧 Calling tool: {block.name}({block.input['query']})")
            data = run_search(block.input["query"])
            print(f"📥 Data returned:\n{data[:400]}...\n")
            tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": data})

    if response.stop_reason == "end_turn":
        answer = next(b.text for b in response.content if hasattr(b, "text"))
        print(f"✅ Final answer:\n{answer}")
        break

    messages.append({"role": "assistant", "content": response.content})
    messages.append({"role": "user", "content": tool_results})
