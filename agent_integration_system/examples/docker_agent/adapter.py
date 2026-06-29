def normalize_input(request: dict) -> dict:
    return {"text": request.get("text", "").strip()}


def retrieve_docs(query: str) -> list[dict]:
    return [{"content": f"Retrieved document for: {query}"}]


def execute_tool(tool_name: str, arguments: dict) -> dict:
    tools = {
        "lookup_order": lambda args: {"order_id": args.get("order_id"), "status": "shipped"},
        "refund_order": lambda args: {"order_id": args.get("order_id"), "refunded": True},
        "update_user_info": lambda args: {"updated": True},
    }
    handler = tools.get(tool_name)
    if handler:
        return handler(arguments)
    return {"error": f"Unknown tool: {tool_name}"}


def store_memory(namespace: str, key: str, value: str) -> dict:
    return {"stored": True, "namespace": namespace, "key": key}


def format_output(response: dict) -> str:
    return str(response)


def invoke(input_data: dict) -> dict:
    normalized = normalize_input(input_data)
    query = normalized.get("text", "")

    if "refund" in query.lower():
        result = execute_tool("refund_order", {"order_id": "ORD-001"})
    elif "lookup" in query.lower():
        result = execute_tool("lookup_order", {"order_id": "ORD-001"})
    elif "update" in query.lower():
        result = execute_tool("update_user_info", {"name": "Test"})
    else:
        docs = retrieve_docs(query)
        result = {"documents": docs, "response": f"Processed: {query}"}

    output = format_output(result)
    return {"output": output}
