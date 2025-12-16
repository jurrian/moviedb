import streamlit as st
from pathlib import Path


# Load external CSS
def load_css():
    css_path = Path(__file__).resolve().parents[1] / "styles.css"
    if css_path.exists():
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def main_page():
    from misc.utils.version import get_app_version
    from django.conf import settings
    load_css()

    # Initialize trigger
    if "trigger_search" not in st.session_state:
        st.session_state.trigger_search = False

    # Initialize session state from URL if present
    if "search_query" not in st.session_state:
        params = st.query_params
        if "q" in params and params["q"]:
            st.session_state.search_query = params["q"]
            st.session_state.trigger_search = True
        else:
            st.session_state.search_query = ""

    # Callback to update URL when text changes
    def update_url_from_input():
        # Update URL
        val = st.session_state.search_query
        if val:
            st.query_params["q"] = val
            # st.session_state.trigger_search = True # Trigger search on enter/blur
        else:
            if "q" in st.query_params:
                del st.query_params["q"]

    # Handle deferred recommendation updates (e.g. from Netflix page)
    if st.session_state.get("recommendations_need_update") and st.session_state.get("user"):
        from movies.search import update_user_recommendations
        update_user_recommendations(st.session_state["user"])
        st.session_state["recommendations_need_update"] = False

    # --- Header Section ---
    st.markdown("""
        <div class="title-container">
            <h1 class="gradient-title">🎬 MovieDB</h1>
            <p class="subtitle">Discover your next favorite story with AI-powered semantic search.</p>
        </div>
    """, unsafe_allow_html=True)


    # --- Search Input ---
    query = st.text_area(
        "Describe what you want to watch:",
        height=150, # Slightly taller for dominance
        key="search_query", 
        help="Type a description of the plot, mood, or setting you are looking for.",
        on_change=update_url_from_input
    )

    with st.expander("⚙️ Search Options", expanded=False):
        top_k = st.slider("Number of results", min_value=5, max_value=50, value=10, step=5)

    # --- Example Queries ---
    st.markdown("### Try it now yourself")
    
    examples = [
        ("⚔️", "Gritty medieval series where a king fights vikings"),
        ("🍿", "Action movies I can watch with my girlfriend, who loves romantic drama"),
        ("🤖", "Cyberpunk anime with philosophical themes"),
        ("🏙️", "Feel-good 90s rom-com playing in New York"),
    ]



    # Display examples as 2x2 grid of buttons
    def update_query(text):
        st.session_state.search_query = text
        st.query_params["q"] = text
        st.session_state.trigger_search = True

    col1, col2 = st.columns(2)
    for i, (icon, ex) in enumerate(examples):
        col = col1 if i % 2 == 0 else col2
        # Use a secondary button style (default) which our CSS targets for subtle look
        col.button(f"{icon}  {ex}", width="stretch", key=f"ex_{i}", on_click=update_query, args=(ex,))

    # --- Search Action ---
    # Centered 'Find Movies' button or full width? Full width is good.
    search_clicked = st.button("🚀 Find Movies", type="primary", width="stretch")
    
    # Initialize persistent state for search results
    if "search_results" not in st.session_state:
        st.session_state.search_results = []
    
    # Check for stale results (missing new annotations) and clear if found
    if st.session_state.search_results:
        first = st.session_state.search_results[0]
        if not hasattr(first, "dist_main"):
            st.warning("Search structure updated. Clearing old results. Please search again.")
            st.session_state.search_results = []
            st.session_state.search_metadata = {}
            
    if "visible_count" not in st.session_state:
        st.session_state.visible_count = top_k

    if search_clicked or st.session_state.trigger_search:
        # Reset the trigger so we don't auto-search again on next reload unless triggered
        st.session_state.trigger_search = False
        
        if query.strip():
            with st.spinner("Analyzing semantic matches..."):
                from movies.search import search_shows
                user_id = st.session_state["user"].id if st.session_state.get("user") else None
                # Always fetch 200 results
                results, structured = search_shows(query.strip(), top_k=200, user=user_id)
                if settings.DEBUG:
                    st.json(structured)
                # Store results in session state to persist across reruns
                st.session_state.search_results = list(results)
                # Store metadata for explanation
                st.session_state.search_metadata = structured.get("result_metadata_dump") or {
                    "weights_used": structured.get("weights", {}),
                    "alpha": 0.5 # default
                }
                
                # Reset visible count to the user's selected top_k
                st.session_state.visible_count = top_k
        else:
             st.session_state.search_results = []
             st.session_state.search_metadata = {}

    # If no active search results, check if we can populate with user recommendations
    if not st.session_state.search_results and not query.strip() and st.session_state.get("user"):
        from movies.models import UserRecommendation, MotnShow
        rec = UserRecommendation.objects.filter(user=st.session_state["user"]).first()
        if rec and rec.recommended_shows:
             ids = rec.recommended_shows
             shows_map = {s.id: s for s in MotnShow.objects.filter(id__in=ids)}
             results_list = [shows_map[i] for i in ids if i in shows_map]
             st.session_state.search_results = results_list
             st.session_state.visible_count = top_k

    # Display results from session state
    results = st.session_state.search_results

    # TODO: give feedback if ambiguous search
    
    if results:
        st.markdown("<br>", unsafe_allow_html=True)
        header_text = "### 🌟 Recommended based on your history" if not query.strip() and st.session_state.get("user") else "### 🎯 Top Matches"
        st.markdown(header_text)
        if not st.session_state.get("user"):
            col_tip, col_btn = st.columns([0.8, 0.2])
            with col_tip:
                st.info("💡 **Tip:** Log in to get personalized recommendations based on your unique taste!")
            with col_btn:
                if st.button("Log in", width="stretch"):
                    st.switch_page("Login")

        st.markdown("---")
        
        # Paginate results
        visible = results[:st.session_state.visible_count]
        
        for show in visible:
            with st.container():
                col1, col2 = st.columns([1, 4])
                
                with col1:
                    if show.poster_urls and "w240" in show.poster_urls:
                        # Use HTML img to avoid enlargement and add margin for alignment
                        st.markdown(
                            f'<img src="{show.poster_urls["w240"]}" style="width: 100%; border-radius: 8px; margin-top: 10px;">', 
                            unsafe_allow_html=True
                        )
                    else:
                        st.empty() # Placeholder or styled blank

                with col2:
                    # Title and Year (Custom div to remove anchor)
                    title_html = f"""<div style="font-size: 1.8rem; font-weight: 700; color: var(--text-color); margin-bottom: 0.5rem; display: flex; align-items: center; justify-content: space-between;">
                            <span>{show.title} <span style='font-size: 1.2rem; color: #888; font-weight: 400;'>({show.year or 'n/a'})</span></span>
                        </div>"""
                    st.markdown(title_html, unsafe_allow_html=True)
                    
                    # Metadata Badges
                    badges = []
                    if show.show_type: badges.append(f"📺 {show.show_type.title()}")
                    if show.age_certification: badges.append(f"🔞 {show.age_certification}")
                    if show.imdb_rating: badges.append(f"⭐ IMDb {show.imdb_rating}")
                    if show.tmdb_rating: badges.append(f"📈 TMDb {show.tmdb_rating}")
                    if show.original_language: badges.append(f"🗣️ {show.original_language.upper()}")
                    
                    st.caption(" · ".join(badges))
                    
                    # Overview
                    st.write(show.overview)

                    # Actions Row (Info + Watch)
                    # Use smaller columns for buttons to keep them close
                    btn_col1, btn_col2, _ = st.columns([0.35, 0.25, 0.4])

                    with btn_col1:
                         # Watch Link
                        try:
                            if show.streaming_options and "nl" in show.streaming_options and show.streaming_options["nl"]:
                                link = show.streaming_options["nl"][0]["videoLink"]
                                st.link_button("▶️ Watch on Netflix", link, type="secondary")
                        except (KeyError, IndexError, TypeError):
                            pass
                    
                    with btn_col2:
                        # Info Popover
                        # Check if we have explanation data (only if query was run)
                        if hasattr(show, "weighted_distance"):
                            with st.popover("ℹ️ Why?", use_container_width=True):
                                st.markdown("### 🔍 Match Breakdown")
                                st.caption("Lower distance = Better match")
                                st.markdown(f"**Total Score:** `{show.weighted_distance:.3f}`")
                                
                                # Retrieve weights from session state metadata if available
                                weights = {}
                                if "search_metadata" in st.session_state and st.session_state.search_metadata:
                                     weights = st.session_state.search_metadata.get("weights_used", {})

                                # Build data table
                                data = []
                                # Fields to check
                                fields = ["plot", "cast", "genre", "tow", "tags", "meta", "language", "main"]
                                # Mapping for display
                                labels = {
                                    "main": "Hypothetical Match (General)",
                                    "plot": "Plot / Story",
                                    "cast": "Cast & Crew",
                                    "genre": "Genre",
                                    "tone": "Tone / Vibe",
                                    "tags": "Keywords",
                                    "meta": "Metadata (Year/Type)",
                                    "language": "Language"
                                }

                                for key in labels:
                                    attr = f"dist_{key}"
                                    if hasattr(show, attr):
                                        dist = getattr(show, attr)
                                        w = weights.get(key, 0.5) # Default/fallback
                                        # Contribution = w * dist
                                        contrib = w * (dist if dist is not None else 2.0)
                                        
                                        # Formatting
                                        dist_str = f"{dist:.2f}" if dist is not None else "N/A"
                                        
                                        # Highlight strong weights
                                        weight_display = f"**{w:.1f}**" if w > 0.6 else f"{w:.1f}"
                                        
                                        data.append({
                                            "Factor": labels[key],
                                            "Weight": weight_display,
                                            "Dist": dist_str,
                                            "Score": f"{contrib:.2f}"
                                        })
                                
                                # Render table
                                st.dataframe(data, hide_index=True, use_container_width=True)
                                
                                st.info("The Total Score is the sum of all component scores. Shows with the lowest Total Score appear first.")
                                
                                # Deep Analysis Button
                                if st.button("🕵️ Deep Analysis", key=f"analyze_{show.id}", type="primary"):
                                    with st.spinner("Asking AI to explain the match..."):
                                        from movies.search import analyze_search_result
                                        
                                        # Reconstruct component dists dict
                                        comp_dists = {}
                                        for k in labels:
                                            attr = f"dist_{k}"
                                            if hasattr(show, attr):
                                                val = getattr(show, attr)
                                                comp_dists[k] = val if val is not None else 2.0
                                        
                                        analysis = analyze_search_result(
                                            raw_query=st.session_state.search_query,
                                            show_obj=show,
                                            structured=st.session_state.search_metadata.get("structured", {}),
                                            component_dists=comp_dists
                                        )
                                        st.markdown("### 🤖 AI Explanation")
                                        st.markdown(analysis)
                
                st.markdown("---")
        
        # Load More Button
        if st.session_state.visible_count < len(results):
             def load_more():
                 st.session_state.visible_count += top_k
             
             st.button("🔽 Load more results", on_click=load_more, type="secondary", width="stretch")

    elif search_clicked:
         st.warning("No matches found. Try a different description!")
    
    # --- Footer ---
    try:
        version = get_app_version()
    except Exception:
        version = "dev"
        
    st.markdown(
        f"""
        <div class="version-footer">
            <span><a href="https://github.com/jurrian/moviedb/releases/tag/v{version}">MovieDB v{version}</a></span>
            <a href="https://github.com/jurrian/moviedb" target="_blank" class="github-link">
                <svg viewBox="0 0 98 96" xmlns="http://www.w3.org/2000/svg"><path fill-rule="evenodd" clip-rule="evenodd" d="M48.854 0C21.839 0 0 22 0 49.217c0 21.756 13.993 40.172 33.405 46.69 2.427.49 3.316-1.059 3.316-2.362 0-1.141-.08-5.052-.08-9.127-13.59 2.934-16.42-5.867-16.42-5.867-2.184-5.704-5.42-7.17-5.42-7.17-4.448-3.015.324-3.015.324-3.015 4.934.326 7.523 5.052 7.523 5.052 4.367 7.496 11.404 5.378 14.235 4.074.404-3.178 1.699-5.378 3.074-6.6-10.839-1.141-22.243-5.378-22.243-24.283 0-5.378 1.94-9.778 5.014-13.2-.485-1.222-2.184-6.275.486-13.038 0 0 4.125-1.304 13.426 5.052a46.97 46.97 0 0 1 12.214-1.63c4.125 0 8.33.571 12.213 1.63 9.302-6.356 13.427-5.052 13.427-5.052 2.67 6.763.97 11.816.485 13.038 3.155 3.422 5.015 7.822 5.015 13.2 0 18.905-11.404 23.06-22.324 24.283 1.78 1.548 3.316 4.481 3.316 9.126 0 6.6-.08 11.897-.08 13.526 0 1.304.89 2.853 3.316 2.364 19.412-6.52 33.405-24.935 33.405-46.691C97.707 22 75.788 0 48.854 0z"/></svg>
                GitHub
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )

