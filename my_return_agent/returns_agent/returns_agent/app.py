"""Chat UI for the Returns Agent.   Run:  streamlit run app.py   (run python database.py once first)"""

from uuid import uuid4

import streamlit as st

import database
from agent import build_agent

st.set_page_config(page_title="ShopEasy Returns Agent", page_icon="🛍️")


# Streamlit reruns this whole file on every click, so build the agent only once
@st.cache_resource
def get_agent():
    return build_agent()


agent = get_agent()
session_id = st.session_state.setdefault("session_id", str(uuid4()))   # a new browser tab gets a fresh memory


# ---------- sidebar: pick a customer, and approve returns as staff

with st.sidebar:
    customer_id = st.selectbox("Log in as customer", ["C-101", "C-102", "C-103", "C-104", "C-105", "C-106"])

    st.subheader("🧑‍💼 Staff approvals")
    pending = database.get_pending_returns()
    if not pending:
        st.caption("Nothing is waiting for approval.")
    for row in pending:
        st.write(f"**{row['order_id']}** · {row['item']} · {row['details']}")
        if st.button("Approve", key=f"approve-{row['return_id']}"):
            database.update_return_status(row["return_id"], "approved")
            st.rerun()
        if st.button("Reject", key=f"reject-{row['return_id']}"):
            database.update_return_status(row["return_id"], "rejected")
            st.rerun()


# ---------- the chat

st.title("🛍️ ShopEasy Returns Agent")

# Each customer has their own chat on screen
history = st.session_state.setdefault(customer_id, [])


# Turns one message into steps: what the LLM thinks, which tool it asks for, what the tool returns
def get_steps(message):
    steps = []
    if message.type == "ai":
        thinking = message.additional_kwargs.get("reasoning_content")
        if thinking:
            steps.append(("💭 thinks", thinking))
        for call in message.tool_calls:
            steps.append(("🔧 tool", f"{call['name']}({call['args']})"))
    elif message.type == "tool":
        steps.append(("📦 result", message.content))
    return steps


# Shows one step: its label and its text
def show_step(label, text):
    st.markdown(f"**{label}**")
    st.code(text, language=None, wrap_lines=True)


# Shows one message from the history, with its steps folded above it
def show(turn):
    with st.chat_message(turn["role"]):
        if turn.get("steps"):
            with st.expander(f"Agent steps ({len(turn['steps'])})"):
                for label, text in turn["steps"]:
                    show_step(label, text)
        st.markdown(turn["content"])


for turn in history:
    show(turn)

text = st.chat_input("Ask about a return or an exchange")
if text:
    history.append({"role": "user", "content": text})
    show(history[-1])

    with st.chat_message("assistant"):
        steps, reply = [], ""
        with st.status("Agent is working...", expanded=True) as status:
            # stream: get each step the moment it happens, not only the final answer
            for update in agent.stream(
                {"messages": [("user", text)]},
                {"configurable": {"thread_id": f"{customer_id}-{session_id}"}},   # memory: one per customer, per tab
                context={"customer_id": customer_id},                              # the tools read who is logged in
                stream_mode="updates",
            ):
                for node in update.values():
                    for message in (node or {}).get("messages", []):
                        for label, step_text in get_steps(message):
                            show_step(label, step_text)          # show it live
                            steps.append((label, step_text))
                        if message.type == "ai" and message.content:
                            reply = message.content              # the last thing the LLM says is the answer
            status.update(label=f"Agent steps ({len(steps)})", state="complete", expanded=False)
        st.markdown(reply)

    history.append({"role": "assistant", "content": reply, "steps": steps})
    st.rerun()      # redraw the page: the staff list may have a new return waiting