import streamlit as st
import hashlib
from cryptography.fernet import Fernet

# --- App Configuration ---
st.set_page_config(page_title="Secure Data Vault", page_icon="🔒")

# --- Security Setup ---
if 'fernet_key' not in st.session_state:
    st.session_state.fernet_key = Fernet.generate_key()
    st.session_state.cipher = Fernet(st.session_state.fernet_key)

# --- Data Storage ---
if 'vault' not in st.session_state:
    st.session_state.vault = {}  # {id: {'data': encrypted, 'passkey': hashed}}
if 'attempts' not in st.session_state:
    st.session_state.attempts = {}  # {id: failed_attempt_count}

# --- Helper Functions ---
def hash_passkey(passkey):
    return hashlib.sha256(passkey.encode()).hexdigest()

def generate_id():
    return hashlib.sha1(str(len(st.session_state.vault)).encode()).hexdigest()[:8]

# --- Page Navigation ---
def show_home():
    st.header("🔐 Secure Data Vault")
    st.write("""
    Store sensitive information securely:
    1. **Encrypt** data with your passkey
    2. **Retrieve** with the same passkey
    3. 3 failed attempts will require reauthorization
    """)

def show_store():
    st.header("📥 Store Data")
    data = st.text_area("Enter your secret data:", height=150)
    passkey = st.text_input("Create a passkey:", type="password")
    
    if st.button("Encrypt & Store"):
        if not data or not passkey:
            st.error("Both fields are required!")
        else:
            data_id = generate_id()
            encrypted = st.session_state.cipher.encrypt(data.encode()).decode()
            st.session_state.vault[data_id] = {
                'data': encrypted,
                'passkey': hash_passkey(passkey)
            }
            st.success(f"✅ Data stored securely! Your ID: `{data_id}`")
            st.code(f"Save this ID to retrieve later:\n{data_id}")

def show_retrieve():
    st.header("📤 Retrieve Data")
    data_id = st.text_input("Enter your data ID:")
    passkey = st.text_input("Enter your passkey:", type="password")
    
    if st.button("Decrypt"):
        if not data_id or not passkey:
            st.error("Both fields are required!")
            return
            
        if data_id not in st.session_state.vault:
            st.error("Invalid data ID!")
            return
            
        entry = st.session_state.vault[data_id]
        st.session_state.attempts[data_id] = st.session_state.attempts.get(data_id, 0) + 1
        
        if st.session_state.attempts[data_id] > 3:
            st.session_state.current_page = "login"
            st.rerun()
            
        if entry['passkey'] == hash_passkey(passkey):
            decrypted = st.session_state.cipher.decrypt(entry['data'].encode()).decode()
            st.session_state.attempts[data_id] = 0
            st.success("✅ Decrypted successfully!")
            st.text_area("Your data:", decrypted, height=200)
        else:
            remaining = 3 - st.session_state.attempts[data_id]
            st.error(f"❌ Wrong passkey! {remaining} attempts remaining")
            if remaining <= 0:
                st.warning("🔒 Account locked - redirecting to login...")
                st.session_state.current_page = "login"
                st.rerun()

def show_login():
    st.header("🔑 Reauthorization Required")
    admin_key = st.text_input("Enter admin password:", type="password")
    
    if st.button("Unlock"):
        if admin_key == "secureadmin123":  # In production, use env variable
            for id in st.session_state.attempts:
                st.session_state.attempts[id] = 0
            st.session_state.current_page = "retrieve"
            st.rerun()
        else:
            st.error("Incorrect admin password!")

# --- Main App Flow ---
if 'current_page' not in st.session_state:
    st.session_state.current_page = "home"

pages = {
    "home": show_home,
    "store": show_store,
    "retrieve": show_retrieve,
    "login": show_login
}

# Sidebar navigation
with st.sidebar:
    st.title("Navigation")
    if st.session_state.current_page != "login":
        if st.button("🏠 Home"):
            st.session_state.current_page = "home"
        if st.button("📥 Store Data"):
            st.session_state.current_page = "store"
        if st.button("📤 Retrieve Data"):
            st.session_state.current_page = "retrieve"

# Show current page
pages[st.session_state.current_page]()