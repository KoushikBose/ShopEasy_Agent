"""The 4 tools of the Returns Agent.

    get_orders        reads  the customer's orders        (database.py)
    search_knowledge  reads  the handbook or the catalog  (retrieval.py)
    book_return       acts   books a return,   if the guardrails pass
    book_exchange     acts   books an exchange, if the guardrails pass

The LLM reads each tool's docstring to decide when to use it.
runtime.context["customer_id"] is the logged-in customer. The LLM cannot change it.
"""

from typing import Literal

from langchain.tools import tool, ToolRuntime

import database
from retrieval import search


# ---------- tools that read

@tool
def get_orders(runtime: ToolRuntime) -> list:
    """Get all orders of the customer, with any return or exchange booked."""
    return database.get_customer_orders(runtime.context["customer_id"])


@tool
def search_knowledge(query: str, source: Literal["handbook", "catalog"]) -> str:
    """Search the handbook for return rules, or the catalog for product details."""
    return search(query, source)


# ---------- guardrails: the same 3 checks for every return and exchange

# Returns the reason to refuse, or None if all checks pass
def check_guardrails(order):
    if order is None:
        return "Refused: this is not the customer's order."
    if database.is_return_booked(order["order_id"]):
        return "Refused: a return or exchange is already booked for this order."
    if order["category"] == "electronics":
        return "Refused: electronics cannot be returned or exchanged."
    return None


# ---------- tools that act

@tool
def book_return(order_id: str, runtime: ToolRuntime) -> str:
    """Book a return and refund for an order."""
    order = database.get_order_for_customer(order_id, runtime.context["customer_id"])

    # 1. Guardrails: stop here if the return is not allowed
    refusal = check_guardrails(order)
    if refusal:
        return refusal

    price = order["price"]

    # 2. Big refund: save it, but a staff member must approve (human in the loop)
    if price > 10000:
        database.add_return(order_id, "return", "waiting_for_staff", f"Refund of Rs {price}")
        return "Not refused: refunds above Rs 10,000 need staff approval. Tell the customer a team member will review it."

    # 3. Normal refund: save it as approved
    else:
        database.add_return(order_id, "return", "approved", f"Refund of Rs {price}")
        return f"Return booked for {order['item']}. Pickup within 2 working days. Refund of Rs {price} after the quality check."


@tool
def book_exchange(order_id: str, new_size: str, runtime: ToolRuntime) -> str:
    """Exchange an order for a different size."""
    order = database.get_order_for_customer(order_id, runtime.context["customer_id"])

    # 1. Guardrails: stop here if the exchange is not allowed
    refusal = check_guardrails(order)
    if refusal:
        return refusal

    item = order["item"]
    old_size = order["size"]

    # 2. Only items with a size (clothing, footwear) can be exchanged
    if old_size is None:
        return "Refused: only clothing and footwear can be exchanged for another size."

    # 3. The new size must be in stock
    elif not database.is_in_stock(item, new_size):
        return f"Out of stock: {item} is not available in size {new_size}. A return for a refund is possible instead."

    # 4. All good: take one from stock and save the exchange
    else:
        database.reduce_stock(item, new_size)
        database.add_return(order_id, "exchange", "approved", f"Size {old_size} to size {new_size}")
        return f"Exchange booked: {item} in size {new_size} will be delivered when size {old_size} is picked up."