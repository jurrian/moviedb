import streamlit as st


def login_page():
    from misc.utils.auth import send_magic_link_email
    
    st.title("Login")
    
    # Check if logged in
    user = st.session_state.get("user")
    if user:
        st.success(f"You are logged in as **{user.username}**.")
        if st.button("Logout", type="primary"):
            from misc.utils.auth import logout_user
            
            # Use the cookie manager initialized in main.py
            cookies = st.session_state.get("cookies")
            if cookies:
                logout_user(cookies.get("sessionid"))
                if "sessionid" in cookies:
                    del cookies["sessionid"]
                    cookies.save()
            
            if "user" in st.session_state:
                del st.session_state["user"]
            st.session_state.search_results = []
            st.rerun()
        return

    if st.query_params.get("invalid"):
        st.error("Old login link or PIN used, please request a new login link.", icon="⚠️")

    with st.form("login_form"):
        email = st.text_input("Email")
        submit = st.form_submit_button("Send email")

    if submit and email:
        send_magic_link_email(email)
        st.success("Login email sent!")
