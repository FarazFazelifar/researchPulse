import threading
import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from streamlit_lottie import st_lottie
import requests
from streamlit_echarts import st_echarts
from streamlit_extras.metric_cards import style_metric_cards 
from streamlit_tags import st_tags
import random
import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from streamlit_lottie import st_lottie
import requests
from streamlit_echarts import st_echarts
import asyncio
import time
from datetime import datetime

# Import the main function from the PubMed API script
from utils.PMC_API import main as pmc_main
from utils.visuals import *

st.set_page_config(layout="wide")

with open("utils/style.html") as f:
    style = f.read()

st.markdown(style, unsafe_allow_html=True)


# Initialize session state variables with default values if they don't exist
if 'query' not in st.session_state:
    st.session_state.query = ""

if 'max_results' not in st.session_state:
    st.session_state.max_results = 10

if 'sort_by' not in st.session_state:
    st.session_state.sort_by = 'relevance'

if 'start_date' not in st.session_state:
    st.session_state.start_date = None

if 'end_date' not in st.session_state:
    st.session_state.end_date = None
    
def run_async_task(query, max_results, sort_by, start_year, end_year):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(pmc_main(query, max_results, sort_by, start_year, end_year))
    except Exception as e:
        st.error(f"An error occurred while fetching data: {str(e)}")
    finally:
        loop.close()

if 'page' not in st.session_state:
    st.session_state.page = "landing"

def change_page(page):
    st.session_state.page = page

def generate_sample_data(num_records=100):
    titles = [
        "Breaking the in-crowd", "Machine Learning for IoT", "A Review of Digital Twins",
        "Hybrid Twins Modeling", "RGB Color Model: Efficiency"
    ]
    abstracts = [
        "Augmented reality (AR) has emerged as a transformative technology...",
        "The Internet of Things (IoT) has revolutionized how we interact with...",
        "This review focuses on the rapidly evolving field of digital twins...",
        "Monitoring a deep geological repository for nuclear waste disposal...",
        "This paper presents a comprehensive analysis of the RGB color model..."
    ]
    journals = [
        "Light, science & applications", "Sensors (Basel, Switzerland)",
        "Nature", "Science", "IEEE Transactions on Pattern Analysis and Machine Intelligence"
    ]
    countries = ["USA", "Iran", "China", "Germany", "Japan", "UK", "Canada", "Australia", "France", "Italy"]
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    data = []

    for _ in range(num_records):
        title = random.choice(titles)
        abstract = random.choice(abstracts)
        journal = random.choice(journals)
        country = random.choice(countries)
        
        authors = ", ".join(random.sample([
            "Smith J", "Johnson A", "Williams B", "Brown C", "Jones D", 
            "Garcia E", "Miller F", "Davis G", "Rodriguez H", "Martinez I"
        ], random.randint(1, 5)))
        
        year = random.randint(2020, 2024)
        month = random.choice(months)
        
        citations = random.randint(0, 1000)
        doi = f"10.{random.randint(1000, 9999)}/s{random.randint(10000, 99999)}-{random.randint(100, 999)}-{random.randint(10000, 99999)}-{random.randint(1, 9)}"
        
        data.append({
            "title": title,
            "abstract": abstract,
            "authors": authors,
            "journal": journal,
            "year": year,
            "month": month,
            "doi": doi,
            "country": country,
            "citations": citations
        })
    
    return pd.DataFrame(data)

# Function to load data from SQLite database
@st.cache_resource
def get_database_connection():
    return sqlite3.connect('articles.db', check_same_thread=False)

@st.cache_data
def load_data(query):
    #return generate_sample_data(500)
    conn = get_database_connection()
    df = pd.read_sql_query(query, conn)
    return df

# Load all data initially
df = load_data("SELECT * FROM articles")

def load_lottie_url(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

def landing_page():
    st.markdown('<h1 class="big-font">ResearchPulse</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subheader">Discover Insights from Scientific Literature</p>', unsafe_allow_html=True)
    
    # Display error message if there is one
    if 'error_message' in st.session_state and st.session_state.error_message:
        st.error(st.session_state.error_message)
        st.session_state.error_message = None  # Clear the error message after displaying

    # Load and display the Lottie animation
    lottie_url = "https://assets5.lottiefiles.com/packages/lf20_fcfjwiyb.json"
    lottie_json = load_lottie_url(lottie_url)
    st_lottie(lottie_json, speed=1, height=300, key="landing_animation")
    
    col1, col2, col3 = st.columns([1.5, 2, 1.5])

    with col2:
        # Basic query input
        query = st.text_input("Enter your research query:", key="search_query")
        
        # Year range input
        current_year = datetime.now().year
        col_start, col_end = st.columns(2)
        with col_start:
            start_year = st.number_input("Start Year", min_value=1900, max_value=current_year - 1, value=2000, step=1)
        with col_end:
            end_year = st.number_input("End Year", min_value=1900, max_value=current_year, value=current_year, step=1)
        
        # Sorting options
        sort_options = {
            "Relevance (Newest First)": "",
            "Citations (Highest First)": "CITED desc",
        }
        sort_by = st.selectbox("Sort results by:", options=list(sort_options.keys()), index=0)
        
        # Number of results
        max_results = st.slider("Number of papers to retrieve:", min_value=5, max_value=150, value=75, step=5)
        
        # Advanced Search Dropdown
        with st.expander("Advanced Search Options"):
            st.markdown("### Refine your search")
            
            # Publication types
            pub_types = st.multiselect(
                "Select publication types:",
                ["RESEARCH ARTICLE", "REVIEW", "BOOK", "EDITORIAL", "LECTURE", "CASE REPORT"],
                default=["RESEARCH ARTICLE"]
            )

            # Open Access filter
            open_access = st.checkbox("Only show Open Access articles")

            # Author search
            authors = st_tags(
                label='Enter author names:',
                text='Type an author name and press enter',
                value=[],
                suggestions=['Smith J', 'Johnson A', 'Williams B'],
                maxtags=5,
                key='authors'
            )

            # Journal search
            journals = st_tags(
                label='Enter journal names:',
                text='Type a journal name and press enter',
                value=[],
                suggestions=['Nature', 'Science', 'Cell'],
                maxtags=5,
                key='journals'
            )

        if st.button("Search"):
            if query or pub_types or open_access or authors or journals:
                # Construct advanced search query
                advanced_query = []
                
                if query:
                    advanced_query.append(f"({query})")
                if pub_types:
                    advanced_query.append("(" + " OR ".join([f'PUB_TYPE:"{pub_type}"' for pub_type in pub_types]) + ")")
                if open_access:
                    advanced_query.append("OPEN_ACCESS:Y")
                if authors:
                    advanced_query.append("(" + " OR ".join([f'AUTH:"{author}"' for author in authors]) + ")")
                if journals:
                    advanced_query.append("(" + " OR ".join([f'JOURNAL:"{journal}"' for journal in journals]) + ")")

                final_query = " AND ".join(advanced_query)

                st.session_state.query = final_query
                st.session_state.sort_by = sort_options[sort_by]
                st.session_state.max_results = max_results
                st.session_state.start_year = start_year
                st.session_state.end_year = end_year
                st.session_state.page = "loading"
                st.session_state.original_query = query
                st.rerun()
            else:
                st.warning("Please enter at least one search term or select a filter.")
                
def loading_page():
    st.markdown('<h2 class="section-header">Fetching Research Data</h2>', unsafe_allow_html=True)
    
    # Load and display the Lottie animation
    lottie_research = load_lottie_url("https://assets5.lottiefiles.com/packages/lf20_1a8dx7zj.json")
    st_lottie(lottie_research, speed=1, height=300, key="loading_animation")

    # List of research tips
    tips = [
        "📊 Did you know? The average number of authors per paper has increased over time in most fields.",
        "🧠 Tip: Use boolean operators (AND, OR, NOT) to refine your search query.",
        "🤯 Fun fact: The longest scientific paper title on record contains 870 characters!",
        "⚠️ Remember: Always critically evaluate the sources and methodology of research papers.",
        "🔔 Tip: Set up citation alerts to stay updated on new papers in your field of interest.",
        "📜 Did you know? 'Peer review' as a standard practice only became widespread in the 1970s.",
        "📚 Tip: Use reference management software to organize your research materials efficiently.",
        "🏆 Fun fact: The most cited scientific paper has over 300,000 citations!",
        "🌐 Remember: Interdisciplinary research often leads to groundbreaking discoveries.",
        "🎓 Tip: Attend conferences to network and stay current with the latest research in your field.",
    ]

    # Display rotating tips
    tip_placeholder = st.empty()
    
    # Run the PMC API script in the background
    try:
        with st.spinner("Analyzing scientific literature..."):
            thread = threading.Thread(target=run_async_task, args=(
                st.session_state.query, 
                st.session_state.max_results, 
                st.session_state.sort_by,
                st.session_state.start_year,
                st.session_state.end_year
            ))
            thread.start()
            
            # Display rotating tips while waiting for the API call to complete
            start_time = time.time()
            while thread.is_alive():
                elapsed_time = time.time() - start_time
                tip_index = int(elapsed_time / 3) % len(tips)
                tip_placeholder.info(f"{tips[tip_index]}")
                time.sleep(0.1)  # Short sleep to prevent excessive CPU usage
            
            # Ensure the thread is complete
            thread.join()
            
            # Check if data was actually saved
            conn = sqlite3.connect('articles.db')
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM articles")
            count = cursor.fetchone()[0]
            conn.close()
            
            if count > 0:
                st.success("Data successfully fetched and processed!")
                time.sleep(2)  # Give users time to see the success message
                st.session_state.page = "dashboard"
                st.rerun()
            else:
                raise Exception("No data was saved to the database.")
                
    except Exception as e:
        st.error(f"An error occurred while fetching data: {str(e)}")
        st.session_state.error_message = f"Error: {str(e)}. Please try again or refine your search query."
        time.sleep(3)  # Give users time to see the error message
        st.session_state.page = "landing"
        st.rerun()

def dashboard_page():
    st.markdown('<h1 class="big-font">ResearchPulse</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subheader">Advanced Research Analytics Dashboard</p>', unsafe_allow_html=True)
    
    st.markdown('<h3 class="section-header"> You searched for:</h3>', unsafe_allow_html=True)
    
    col_q, col_b = st.columns([9, 1])
    
    with col_q:
        st.markdown(f'<p class="main-body">{st.session_state.original_query}!</>', unsafe_allow_html=True)
        
    
    with col_b:
        if st.button("New Search 🔍", key="00"):
            st.session_state.page = "landing"
            st.rerun()

    # Load data
    conn = sqlite3.connect('articles.db')
    df = pd.read_sql_query("SELECT * FROM articles", conn)
    conn.close()

    # Filters
    st.markdown('<h2 class="section-header">Research Filters</h2>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        start_year, end_year = st.slider("Publication Year Range", 
                                         min_value=int(df['year'].min()), 
                                         max_value=int(df['year'].max()), 
                                         value=(int(df['year'].min()), int(df['year'].max())))
    with col2:
        selected_journals = st.multiselect("Select Journals", options=df['journal'].unique())
    with col3:
        selected_countries = st.multiselect("Choose Countries", options=df['country'].unique())        

    # Apply filters and sorting
    filtered_df = df[
        (df['year'].astype(int).between(start_year, end_year)) &
        (df['journal'].isin(selected_journals) if selected_journals else True) &
        (df['country'].isin(selected_countries) if selected_countries else True)
    ]


    # Key Metrics
    st.markdown('<h2 class="section-header">Key Metrics</h2>', unsafe_allow_html=True)
    metric_cols = st.columns(5)
    metrics = [
        {"label": "Total Publications", "value": len(filtered_df)},
        {"label": "Unique Authors", "value": filtered_df['authors'].str.split(', ').explode().nunique()},
        {"label": "Unique Journals", "value": filtered_df['journal'].nunique()},
        {"label": "Total Citations", "value": filtered_df['citations'].sum()},
        {"label": "Countries Represented", "value": filtered_df['country'].nunique()}
    ]
    for i, metric in enumerate(metrics):
        with metric_cols[i]:
            st.metric(label=metric["label"], value=f"{metric['value']:,}")
    style_metric_cards(background_color="#FFFFFF", border_left_color="#1E90FF", border_color="#4682B4")

    # Research Insights
    st.markdown('<h2 class="section-header">Research Insights</h2>', unsafe_allow_html=True)
    tabs = st.tabs(["📊 Publication Trends", "📈 Citation Analysis", "🌍 Geographical Insights", "🤝 Author Collaboration", "🏆 Top Papers"])
    
    with tabs[0]:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Journal Distribution")
            fig_journal = plot_journal_distribution(filtered_df)
            st.plotly_chart(fig_journal, use_container_width=True, config={'displayModeBar': False})

        with col2:
            st.subheader("Publications Over Time")
            chart = plot_yearly_publications(filtered_df)
            st.altair_chart(chart, use_container_width=True)

    with tabs[1]:
        st.subheader("Journal Impact: Citations vs Publications")
        fig_citations = plot_citations_by_journal(filtered_df)
        st.plotly_chart(fig_citations, use_container_width=True)

    with tabs[2]:
        st.subheader("Geographical Distribution of Research")
        fig_map = plot_country_publications(filtered_df)
        st.plotly_chart(fig_map, use_container_width=True)

    with tabs[3]:
        st.subheader("Author Collaboration Network")
        fig_network = plot_collaboration_network(filtered_df)
        st.plotly_chart(fig_network, use_container_width=True)

    with tabs[4]:
        st.subheader("Top 10 Most Cited Papers")
        fig_top_papers = plot_top_cited_papers(filtered_df)
        st.plotly_chart(fig_top_papers, use_container_width=True)

    # Word Cloud
    st.markdown('<h2 class="section-header">Trending Research Topics</h2>', unsafe_allow_html=True)
    text = " ".join(filtered_df['abstract'])
    fig_wordcloud = plot_wordcloud(text)
    st.plotly_chart(fig_wordcloud, use_container_width=True, config={'displayModeBar': False})

    # Interactive Data Table with ECharts
    st.markdown('<h2 class="section-header">Publication and Citation Trends</h2>', unsafe_allow_html=True)
    yearly_data = filtered_df.groupby('year').agg({
        'title': 'count',
        'citations': 'sum'
    }).reset_index()
    options = {
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "cross"}},
        "legend": {"data": ["Publications", "Citations"]},
        "xAxis": [{"type": "category", "data": yearly_data['year'].tolist()}],
        "yAxis": [
            {"type": "value", "name": "Publications", "position": "left"},
            {"type": "value", "name": "Citations", "position": "right"}
        ],
        "series": [
            {
                "name": "Publications",
                "type": "bar",
                "data": yearly_data['title'].tolist()
            },
            {
                "name": "Citations",
                "type": "line",
                "yAxisIndex": 1,
                "data": yearly_data['citations'].tolist()
            }
        ]
    }
    st_echarts(options=options, height="400px")

    # Author impact analysis
    st.markdown('<h2 class="section-header">Top Authors by Citation Impact</h2>', unsafe_allow_html=True)
    author_impact = filtered_df.assign(authors=filtered_df['authors'].str.split(', ')).explode('authors')
    author_impact = author_impact.groupby('authors').agg({
        'citations': 'sum',
        'title': 'count'
    }).reset_index()
    author_impact['avg_citations'] = author_impact['citations'] / author_impact['title']
    author_impact = author_impact.sort_values('avg_citations', ascending=False).head(20)

    fig_author_impact = px.bar(author_impact, 
                               x='authors', y='avg_citations', 
                               color='citations',
                               hover_data=['title'],
                               labels={'avg_citations': 'Average Citations per Paper',
                                       'authors': 'Author',
                                       'citations': 'Total Citations',
                                       'title': 'Number of Publications'},
                               title='Top 20 Authors by Average Citations per Paper')
    fig_author_impact.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_author_impact, use_container_width=True)

    # Interactive paper explorer
    st.markdown('<h2 class="section-header">Paper Explorer</h2>', unsafe_allow_html=True)


    col1, col2 = st.columns(2)

    with st.container():

        with col1:
            st.markdown('<p class="paper-header">Paper List</p>', unsafe_allow_html=True)

            # Sorting options
            sort_options = {
                "Date (Newest First)": ("year", False),
                "Date (Oldest First)": ("year", True),
                "Citations (High to Low)": ("citations", False),
                "Citations (Low to High)": ("citations", True),
            }
            sort_by = st.selectbox("Sort results by:", options=list(sort_options.keys()))

            # Apply sorting based on user selection
            sort_column, ascending = sort_options[sort_by]
            filtered_df = filtered_df.sort_values(by=sort_column, ascending=ascending)

            # Update paper list after sorting
            paper_list = [f"{row['title']} (Citations: {row['citations']})" 
                        for _, row in filtered_df.iterrows()]

            # Use a fixed-height container for the dropdown
            selected_paper = st.selectbox("Select a paper to review", paper_list)
            

        with col2:
            st.markdown('<p class="paper-header">Paper Details</p>', unsafe_allow_html=True)
            
            if selected_paper:
                # Extract the title from the selected paper string
                selected_title = selected_paper.split(" (Citations:")[0]
                
                # Find the paper in the filtered DataFrame
                selected_paper_data = filtered_df[filtered_df['title'] == selected_title].iloc[0]
                
                st.markdown(f"**Title:** {selected_paper_data['title']}")
                st.markdown(f"**DOI:** {selected_paper_data['doi']}")
                st.markdown(f"**Authors:** {selected_paper_data['authors']}")
                st.markdown(f"**Journal:** {selected_paper_data['journal']}")
                st.markdown(f"**Year:** {selected_paper_data['year']}")
                st.markdown(f"**Citations:** {selected_paper_data['citations']}")
                st.markdown(f"**Country:** {selected_paper_data['country']}")
                st.markdown("**Abstract:**")
                st.markdown(selected_paper_data['abstract'])
            else:
                st.write("Select a paper to view details")
            st.markdown('</div>', unsafe_allow_html=True)

        
    # User feedback
    st.markdown('<h2 class="section-header">Your Feedback</h2>', unsafe_allow_html=True)
    st.markdown('<div class="info-box">Your feedback helps us improve! Please rate your experience and share any suggestions.</div>', unsafe_allow_html=True)
    user_rating = st.slider("How would you rate this dashboard?", min_value=1, max_value=5, value=3)
    st.write(f"You rated the dashboard: {user_rating} out of 5")

    feedback = st.text_area("Please provide any additional feedback or suggestions:")
    if st.button("Submit Feedback"):
        st.success("Thank you for your feedback! We appreciate your input.")

    # Download button
    st.markdown('<h2 class="section-header">Download Data</h2>', unsafe_allow_html=True)
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        label="📥 Download data as CSV",
        data=csv,
        file_name="research_data.csv",
        mime="text/csv",
    )
    
    if st.button("New Search 🔍", key="01"):
        st.session_state.page = "landing"
        st.rerun()

def main():
    # Initialize session state
    if 'page' not in st.session_state:
        st.session_state.page = "landing"

    # Page routing
    if st.session_state.page == "landing":
        landing_page()
    elif st.session_state.page == "loading":
        loading_page()
    elif st.session_state.page == "dashboard":
        dashboard_page()

if __name__ == "__main__":
    main()