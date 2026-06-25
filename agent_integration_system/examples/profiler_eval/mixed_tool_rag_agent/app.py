def retrieve_docs(query):
    return [f"doc:{query}"]


def execute_refund(order_id):
    return {"order_id": order_id, "refunded": True}


def remember_user_preference(user_id, preference):
    return {"user_id": user_id, "preference": preference}
