"""Streamlit UI for the document verification blockchain service."""

import os

import requests
import streamlit as st

DEFAULT_API_BASE_URL = os.getenv("BLOCKCHAIN_API_URL", "http://127.0.0.1:5000")
REQUEST_TIMEOUT_SECONDS = 10

st.set_page_config(
    page_title="Document Verification Blockchain",
    page_icon=":ledger:",
    layout="wide",
)

st.markdown(
    """
    <style>
    .hero {
        padding: 1.25rem 1.5rem;
        border-radius: 1rem;
        background: linear-gradient(135deg, #f5f1e8 0%, #dfe9f3 100%);
        border: 1px solid #d6d3cc;
        margin-bottom: 1rem;
    }
    .status-card {
        padding: 1rem;
        border-radius: 0.75rem;
        background: #faf8f4;
        border: 1px solid #e6e1d7;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def api_request(method, path, payload=None):
    """Call the Flask backend and normalize the response for the UI."""
    base_url = st.session_state.get("api_base_url", DEFAULT_API_BASE_URL).rstrip("/")
    url = f"{base_url}{path}"
    try:
        response = requests.request(
            method=method,
            url=url,
            json=payload,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        return None, f"Could not reach the backend: {exc}"

    try:
        data = response.json()
    except ValueError:
        data = None

    if response.ok:
        return data, None

    if isinstance(data, dict):
        return None, data.get("error") or data.get("message") or "Request failed."
    return None, f"Request failed with status code {response.status_code}."


def load_dashboard_data():
    """Fetch chain and pending queue data for dashboard metrics."""
    chain_data, chain_error = api_request("GET", "/get_chain")
    pending_data, pending_error = api_request("GET", "/pending_documents")
    return chain_data, chain_error, pending_data, pending_error


st.session_state.setdefault("api_base_url", DEFAULT_API_BASE_URL)

st.title("Document Verification Blockchain")
st.markdown(
    """
    <div class="hero">
        Register document fingerprints, mine them into blocks, and verify later
        that a document hash exists on-chain.
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Settings")
    st.text_input("Backend API URL", key="api_base_url")
    page = st.radio(
        "Navigate",
        (
            "Dashboard",
            "Add Document",
            "Pending Documents",
            "Verify Document",
            "Blockchain Explorer",
        ),
    )

chain_data, chain_error, pending_data, pending_error = load_dashboard_data()

if page == "Dashboard":
    col1, col2 = st.columns(2)
    with col1:
        length = chain_data["length"] if chain_data else 0
        st.metric("Chain Length", length)
    with col2:
        pending_count = pending_data["pending_count"] if pending_data else 0
        st.metric("Pending Documents", pending_count)

    if chain_error:
        st.error(chain_error)
    if pending_error:
        st.error(pending_error)

    st.subheader("Quick Action")
    if st.button("Mine Pending Documents", use_container_width=True):
        mine_data, mine_error = api_request("GET", "/mine_block")
        if mine_error:
            st.error(mine_error)
        else:
            st.success(
                f"Mined block #{mine_data['index']} with "
                f"{len(mine_data['documents'])} document(s)."
            )
            st.json(mine_data)

    st.subheader("Project Overview")
    st.markdown(
        """
        <div class="status-card">
            Use the sidebar to queue documents, inspect pending records, verify
            a hash, or browse the blockchain.
        </div>
        """,
        unsafe_allow_html=True,
    )

elif page == "Add Document":
    st.header("Add Document Record")
    with st.form("add_document_form"):
        document_hash = st.text_input("Document Hash (SHA-256)", max_chars=128)
        document_name = st.text_input("Document Name")
        issuer = st.text_input("Issuer")
        owner = st.text_input("Owner")
        document_type = st.text_input("Document Type")
        issued_at = st.text_input("Issued At")
        submitted = st.form_submit_button("Queue Document")

    if submitted:
        payload = {
            "document_hash": document_hash,
            "document_name": document_name,
            "issuer": issuer,
            "owner": owner,
            "document_type": document_type,
            "issued_at": issued_at,
        }
        data, error = api_request("POST", "/add_document", payload=payload)
        if error:
            st.error(error)
        else:
            st.success(data["message"])
            st.caption(f"Pending documents: {data['pending_count']}")

elif page == "Pending Documents":
    st.header("Pending Documents")
    if pending_error:
        st.error(pending_error)
    elif pending_data["pending_documents"]:
        st.dataframe(pending_data["pending_documents"], use_container_width=True)
    else:
        st.info("No pending documents are waiting to be mined.")

elif page == "Verify Document":
    st.header("Verify Document")
    with st.form("verify_document_form"):
        document_hash = st.text_input("Document Hash")
        submitted = st.form_submit_button("Verify")

    if submitted:
        if not document_hash.strip():
            st.error("Document hash is required.")
        else:
            data, error = api_request("GET", f"/verify_document/{document_hash.strip()}")
            if error:
                st.error(error)
            elif data["verified"]:
                st.success(data["message"])
                st.write(f"Block Index: {data['block_index']}")
                st.write(f"Timestamp: {data['timestamp']}")
                st.json(data["document"])
            else:
                st.warning(data["message"])

elif page == "Blockchain Explorer":
    st.header("Blockchain Explorer")
    if chain_error:
        st.error(chain_error)
    elif chain_data["chain"]:
        for block in reversed(chain_data["chain"]):
            st.subheader(f"Block #{block['index']}")
            st.json(block)
    else:
        st.info("The blockchain is empty.")
