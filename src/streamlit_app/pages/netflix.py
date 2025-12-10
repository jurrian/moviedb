import csv
import io
import re
from collections import defaultdict
from datetime import datetime

import streamlit as st



def parse_netflix_csv(file) -> int:
    from movies.models import MotnShow, UserViewInteraction
    from movies.search import update_user_recommendations
    """
    Parses a Netflix viewing activity CSV and creates/updates UserViewInteractions.
    Returns the number of new interactions created.
    """
    user = st.session_state.get("user")
    if not user:
        st.error("You must be logged in to upload Netflix history.")
        return 0

    # Decode file
    try:
        content = file.getvalue().decode('utf-8')
    except UnicodeDecodeError:
        st.error("Failed to decode file. Please ensure it is a valid UTF-8 CSV.")
        return 0

    reader = csv.DictReader(io.StringIO(content))
    
    # Validate headers
    if not reader.fieldnames or "Title" not in reader.fieldnames or "Date" not in reader.fieldnames:
        st.error("Invalid CSV format. Expected columns: 'Title', 'Date'.")
        return 0

    # Aggregate data
    # Key: show_title, Value: {dates: [], count: 0}
    shows_data = defaultdict(lambda: {'dates': [], 'count': 0})
    
    for row in reader:
        title_raw = row['Title']
        date_str = row['Date']
        
        try:
            date_obj = datetime.strptime(date_str, "%m/%d/%y").date()
        except ValueError:
            continue 

        # Parse title
        # Logic: Look for ": Season \d+" to identify series episodes
        match = re.search(r'^(.*?): Season \d+', title_raw)
        if match:
            show_title = match.group(1)
        else:
            show_title = title_raw
            
        shows_data[show_title]['dates'].append(date_obj)
        shows_data[show_title]['count'] += 1

    new_interactions_count = 0
    
    for show_title, data in shows_data.items():
        dates = sorted(data['dates'])
        first_date = dates[0]
        last_date = dates[-1]
        count = data['count']
        
        # Find MotnShow
        # Try exact case-insensitive match
        motn = MotnShow.objects.filter(title__iexact=show_title).first()
        
        if not motn:
            continue
            
        # Update or Create
        interaction, created = UserViewInteraction.objects.get_or_create(
            user=user,
            show=motn,
            defaults={
                'first_date': first_date,
                'last_date': last_date,
                'viewed_amount': count,
            }
        )
        
        if created:
            new_interactions_count += 1
        else:
            # Update existing interaction
            changed = False
            if not interaction.first_date or first_date < interaction.first_date:
                interaction.first_date = first_date
                changed = True
            if not interaction.last_date or last_date > interaction.last_date:
                interaction.last_date = last_date
                changed = True
            if not interaction.viewed_amount or count > interaction.viewed_amount:
                interaction.viewed_amount = count
                changed = True
            
            if changed:
                interaction.save()

    # Recalculate recommendations
    if new_interactions_count > 0 or len(shows_data) > 0:
        with st.spinner("Updating recommendations..."):
            update_user_recommendations(user)

    return new_interactions_count


def update_rating(interaction_id):
    from movies.models import UserViewInteraction
    from movies.search import update_user_recommendations
    key = f"up_{interaction_id}"
    val = st.session_state.get(key)
    
    # st.feedback("thumbs") returns 1 (Thumbs Up) or 0 (Thumbs Down)
    if val == 1:
        new_rating = 1
    elif val == 0:
        new_rating = -1
    else:
        new_rating = 0
        
    UserViewInteraction.objects.filter(id=interaction_id).update(rating=new_rating)
    
    # Defer feedback update to page transition
    st.session_state["recommendations_need_update"] = True


def render_user_interactions():
    from movies.models import UserViewInteraction
    user = st.session_state.get("user")

    st.header("Your Netflix history")
    
    # Fetch user interactions
    interactions = UserViewInteraction.objects.filter(user=user).select_related('show')
    
    if not interactions.exists():
        st.write("No history found.")
    else:
        st.markdown("Give **thumbs up** what you really liked or **thumbs down** what you didn't like, to improve recommendations. The system learns your preferences from your feedback.")
        st.write(f"Found {interactions.count()} shows:")

        for intr in interactions:
            st.divider()
            c1, c2, c3, c4 = st.columns([2, 5, 2, 1])
            with c1:
                if intr.show.poster_urls and "w92" in intr.show.poster_urls:
                    st.image(intr.show.poster_urls["w92"])
                elif intr.show.poster_urls and "w240" in intr.show.poster_urls:
                    st.image(intr.show.poster_urls["w240"])
                else:
                    st.caption("No Image")
            with c2:
                st.subheader(intr.show.title, anchor=False)
                st.caption(f"{intr.show.year or 'N/A'}")
            with c3:
                st.write(f"Views/episodes:\n{intr.viewed_amount}")
                st.caption(f"Last viewed:  \n{intr.last_date}")
            with c4:
                # Pre-populate feedback state
                feedback_key = f"up_{intr.id}"
                if feedback_key not in st.session_state:
                    if intr.rating == 1:
                        st.session_state[feedback_key] = 1
                    elif intr.rating == -1:
                        st.session_state[feedback_key] = 0
                
                st.feedback("thumbs", key=feedback_key, on_change=update_rating, args=(intr.id,))
            


def upload_netflix():
    st.title("Upload Netflix history")

    st.write("Improve your recommendations by uploading your Netflix viewing history.")

    user = st.session_state.get("user")
    if not user:
        st.info("Log in to add your Netflix history.")
        return

    st.markdown(
        "1. Open [viewing activity in Netflix](https://www.netflix.com/viewingactivity)\n"
        "2. Click download all, bottom right under the activity list\n"
        "3. Upload the downloaded file here\n"
    )
    
    file = st.file_uploader("Upload Netflix viewing activity CSV", type="csv")
    if file:
        new_count = parse_netflix_csv(file)
        if new_count > 0:
            st.success(f"Added {new_count} new movie/series interactions!")
        else:
            st.info("Processed file. No new interactions found (updated existing ones).")

    st.divider()
    render_user_interactions()
