import os
import sys
from pathlib import Path
import streamlit as st
from logger import setup_logging, setup_sentry
from django.conf import settings

# Add project root to sys.path so modules like 'core', 'pages', etc. can be imported
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

@st.cache_resource
def django_setup():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

    import django  # noqa: E402

    django.setup()


def main():
    setup_logging()
    setup_sentry()
    st.set_page_config(
        page_title="MovieDB: AI-powered movie recommendations",
        page_icon="🎬",
        menu_items={
            "Get Help": "https://github.com/jurrian/moviedb",
            "Report a bug": "https://github.com/jurrian/moviedb/issues",
            "About": (
                "## MovieDB\n"
                "AI-powered movie and series recommendations.\n\n"
                "Streamlit + Django app by Jurrian Tromp.\n\n"
                "Github: [github.com/jurrian/moviedb](http://github.com/jurrian/moviedb)"
            ),
        }
    )

    # Safe imports (deferred Django dependency)
    from pages.home import main_page
    from pages.login import login_page
    from pages.netflix import upload_netflix

    # Define pages & navigation immediately to fix initial sidebar state
    login_title = "Login"
    if st.session_state.get("user"):
        login_title = f"Logged in as {st.session_state['user'].username}"

    main_page_obj = st.Page(main_page, icon=":material/home:", title="Home")
    login_page_obj = st.Page(login_page, icon=":material/login:", title=login_title, url_path="login")
    upload_page_obj = st.Page(upload_netflix, icon=":material/upload:", title="Upload Netflix", url_path="upload")

    pg = st.navigation(pages=[main_page_obj, upload_page_obj, login_page_obj], position="top")

    # Initialize Django & Session
    with st.spinner("Starting MovieDB..."):
        django_setup()
        
        # Need auth utils for magic link and cookies
        from misc.utils.auth import start_django_session, setup_cookies
        cookies = setup_cookies()
        st.session_state["cookies"] = cookies

    # Handle magic link login
    params = st.query_params
    if "email" in params and "pin" in params:
        from django.contrib.auth import authenticate
        from misc.utils.auth import ensure_activate_user

        ensure_activate_user(params["email"])
        user = authenticate(username=params["email"], password=params["pin"])
        if user:
            st.session_state["user"] = user
            
            # Create persistent session
            session_key = start_django_session(user)
            
            # Set cookie (persistence)
            cookies["sessionid"] = session_key
            cookies.save()
            
            # Clear sensitive params
            st.query_params.clear()
            st.switch_page(main_page_obj)
        else:
            # We need to manually navigate or show error on login page
            # We can force query params for the login page to pick up
            st.switch_page(login_page_obj)

    pg.run()


if __name__ == "__main__":
    main()