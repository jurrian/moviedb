import os
import sys

import mlflow
import streamlit as st
from django.conf import settings
from streamlit_cookies_manager import EncryptedCookieManager


def login_page():
    if st.query_params.get("invalid"):
        st.error("Old login link or PIN used, please request a new login link.", icon="⚠️")

    with st.form("login_form"):
        email = st.text_input("Email")
        submit = st.form_submit_button("Stuur login email")

    if submit and email:
        from misc.utils.auth import send_magic_link_email
        send_magic_link_email(email)
        st.success("Login email verstuurd!")


def main_page():
    st.title("MovieDB")
    if not st.session_state.get("user"):
        st.caption("Log in to get personalized recommendations based on your taste!")
        st.page_link(login_page_obj, label="Login with Email", icon=":material/login:")
        
    st.subheader("AI-powered Netflix NL recommendations")

    query = st.text_area(
        "Describe what you want to watch:",
        height=100,
        value="gritty medieval series where a king fights vikings",
    )

    top_k = st.slider("Number of results", min_value=5, max_value=50, value=10, step=5)

    if st.button("Search") and query.strip():
        with st.spinner("Searching..."):
            results, structured = search_shows(query.strip(), top_k=top_k, user=1)  # TODO: user=1

            st.json(structured, expanded=False)

        if not results:
            st.warning("No results found.")
        else:
            st.subheader("Results")
            for show in results:
                col1, col2 = st.columns([1, 3])
                col1.image(show.poster_urls["w240"])

                meta_bits = []
                if show.show_type:
                    meta_bits.append(show.show_type)
                if show.age_certification:
                    meta_bits.append(f"Rated {show.age_certification}")
                if show.original_language:
                    meta_bits.append(f"Language: {show.original_language}")
                if show.imdb_rating:
                    meta_bits.append(f"IMDb {show.imdb_rating}")
                if show.tmdb_rating:
                    meta_bits.append(f"TMDb {show.tmdb_rating}")

                with col2.container(height=236, gap="small"):
                    st.markdown(f"### {show.title} ({show.year or 'n/a'})")
                    st.write(show.overview)

                try:
                    col2.page_link(
                        show.streaming_options["nl"][0]["videoLink"],
                        label="Watch on Netflix",
                        icon="▶️",
                    )
                except (KeyError, IndexError):
                    pass

                if meta_bits:
                    col1.caption(" · ".join(str(x) for x in meta_bits))

                # Optional: show genres
                # if show.genres:
                #     if isinstance(show.genres, list):
                #         genres_display = ", ".join(map(str, show.genres))
                #     else:
                #         genres_display = str(show.genres)
                #     st.caption(f"Genres: {genres_display}")

                st.markdown("---")


@st.cache_resource
def django_setup():
    # Adjust these to point to your Django project
    DJANGO_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
    if DJANGO_PROJECT_ROOT not in sys.path:
        sys.path.append(DJANGO_PROJECT_ROOT)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

    import django  # noqa: E402

    django.setup()


def setup_cookies():
    from misc.utils.auth import get_user_from_session_key

    cookies = EncryptedCookieManager(
        prefix="moviedb/",
        password=settings.SECRET_KEY,
    )

    if not cookies.ready():
        st.stop()

    session_key = cookies.get("sessionid")

    # Restore session from Cookie if present
    if session_key:
        session_user = get_user_from_session_key(session_key)
        if session_user:
            st.session_state["user"] = session_user
        else:
            # Invalid session in cookie
            pass

    return cookies


@st.cache_resource(show_spinner=False)
def search_shows(*args, **kwargs):
    from movies.search import search_shows

    return search_shows(*args, **kwargs)


def main():
    django_setup()
    cookies = setup_cookies()

    # Need django_setup first
    from misc.utils.auth import start_django_session

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

    # Handle magic link login
    params = st.query_params
    if "email" in params and "pin" in params:
        from django.contrib.auth import authenticate

        from misc.utils.auth import ensure_activate_user

        user = authenticate(username=params["email"], password=params["pin"])
        if user:
            ensure_activate_user(user)
            st.session_state["user"] = user
            
            # Create persistent session
            session_key = start_django_session(user)
            
            # Set cookie (persistence)
            cookies["sessionid"] = session_key
            cookies.save()
            
            # Clear sensitive params
            st.query_params.clear()
        else:
            st.switch_page(login_page_obj, query_params={"invalid": 1})


    login_title = "Login"
    if st.session_state.get("user"):
        login_title = f"Logged in as {st.session_state['user'].username}"

    # Page definitions
    main_page_obj = st.Page(main_page, icon=":material/home:", title="Home")
    login_page_obj = st.Page(login_page, icon=":material/login:", title=login_title, url_path="login")

    pg = st.navigation(pages=[main_page_obj, login_page_obj], position="top")
    pg.run()


if __name__ == "__main__":
    main()
    