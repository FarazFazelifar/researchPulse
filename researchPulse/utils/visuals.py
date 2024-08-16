import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
import networkx as nx
import altair as alt
import requests
import random
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
import networkx as nx
import altair as alt
import requests

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


def plot_wordcloud(text):
    wordcloud = WordCloud(width=800, height=400, background_color='#f5f5f7', colormap='viridis').generate(text)
    fig = px.imshow(wordcloud, template='plotly_white')
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))
    return fig

def plot_journal_distribution(df):
    journal_counts = df['journal'].value_counts().reset_index()
    journal_counts.columns = ['Journal', 'Count']
    fig = px.treemap(journal_counts, path=['Journal'], values='Count',
                     color='Count', color_continuous_scale='Viridis',
                     title='Journal Distribution')
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=40, b=20),
        font=dict(family="SF Pro Display")
    )
    return fig

def plot_yearly_publications(df):
    yearly_pubs = df.groupby('year').size().reset_index(name='count')
    chart = alt.Chart(yearly_pubs).mark_area(
        line={'color':'darkblue'},
        color=alt.Gradient(
            gradient='linear',
            stops=[alt.GradientStop(color='white', offset=0),
                   alt.GradientStop(color='darkblue', offset=1)],
            x1=1,
            x2=1,
            y1=1,
            y2=0
        )
    ).encode(
        x='year:T',
        y='count:Q'
    ).properties(
        title='Publications Over Time'
    )
    return chart

def plot_collaboration_network(df):
    # Create graph
    G = nx.Graph()
    author_pub_count = {}
    author_citation_count = {}
    for _, row in df.iterrows():
        authors = row['authors'].split(', ')
        citations = int(row['citations'])
        year = int(row['year'])
        for author in authors:
            if author not in author_pub_count:
                author_pub_count[author] = 0
                author_citation_count[author] = 0
            author_pub_count[author] += 1
            author_citation_count[author] += citations
            G.add_node(author, year=year)
        for i in range(len(authors)):
            for j in range(i+1, len(authors)):
                if G.has_edge(authors[i], authors[j]):
                    G[authors[i]][authors[j]]['weight'] += 1
                else:
                    G.add_edge(authors[i], authors[j], weight=1)

    # Select top 100 authors based on citation count
    top_authors = sorted(author_citation_count, key=author_citation_count.get, reverse=True)[:50]
    
    # Create a subgraph with only the top 100 authors
    G = G.subgraph(top_authors)

    # Identify main author (now from the top 100)
    main_author = max(author_citation_count, key=lambda x: author_citation_count[x] if x in top_authors else 0)

    # Custom layout with main author in center
    pos = nx.spring_layout(G, k=0.5, iterations=50)
    pos[main_author] = (0, 0)  # Place main author at center

    # Node size scaling
    citation_counts = [author_citation_count[node] for node in G.nodes()]
    size_scaler = MinMaxScaler(feature_range=(20, 80))
    node_sizes = size_scaler.fit_transform(np.array(citation_counts).reshape(-1, 1)).flatten()

    # Node color scaling (blue gradient)
    color_scaler = MinMaxScaler(feature_range=(0.2, 0.8))
    node_colors = color_scaler.fit_transform(np.array(citation_counts).reshape(-1, 1)).flatten()
    node_colors_rgb = [f'rgb({int(230-150*c)},{int(242-100*c)},{int(255-50*c)})' for c in node_colors]

    # Create edges
    edge_x, edge_y = [], []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color='#D3D3D3'),
        hoverinfo='none',
        mode='lines')

    # Create nodes
    node_x, node_y = [], []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        hoverinfo='text',
        marker=dict(
            showscale=False,
            color=node_colors_rgb,
            size=node_sizes,
            line=dict(width=2, color='#FFFFFF')
        ),
        text=[f'{node}<br>{G.nodes[node]["year"]}' for node in G.nodes()],
        textposition="top center",
        textfont=dict(size=10, color='#505050')
    )

    # Prepare node hover text
    hover_text = []
    for node in G.nodes():
        hover_text.append(f'Author: {node}<br>'
                          f'Year: {G.nodes[node]["year"]}<br>'
                          f'Publications: {author_pub_count[node]}<br>'
                          f'Citations: {author_citation_count[node]}')
    node_trace.hovertext = hover_text

    # Create the layout
    layout = go.Layout(
        showlegend=False,
        hovermode='closest',
        margin=dict(b=20, l=5, r=5, t=40),
        annotations=[],
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor='rgba(248,248,252,1)',
        paper_bgcolor='rgba(248,248,252,1)',
        width=900,
        height=900,
        title="Top 100 Authors Collaboration Network"
    )

    # Create figure
    fig = go.Figure(data=[edge_trace, node_trace], layout=layout)

    # Add subtle glow to main author
    fig.add_trace(go.Scatter(
        x=[pos[main_author][0]], y=[pos[main_author][1]],
        mode='markers',
        marker=dict(
            size=node_sizes[list(G.nodes()).index(main_author)] + 5,
            color='rgba(70,130,180,0.3)',
            line=dict(width=2, color='rgba(70,130,180,0.8)')
        ),
        hoverinfo='skip'
    ))

    # Add interactive highlighting
    for node in G.nodes():
        node_edges = list(G.edges(node))
        highlight_x, highlight_y = [], []
        for edge in node_edges:
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            highlight_x.extend([x0, x1, None])
            highlight_y.extend([y0, y1, None])
        
        fig.add_trace(go.Scatter(
            x=highlight_x, y=highlight_y,
            line=dict(width=2, color='rgba(255,165,0,0.7)'),
            hoverinfo='none',
            mode='lines',
            name=f'Highlight {node}',
            visible=False
        ))

    # Add hover and unhover events for highlighting
    fig.update_traces(
        hovertemplate='%{hovertext}<extra></extra>',
        hoverlabel=dict(bgcolor="white", font_size=12),
        selector=dict(type='scatter', mode='markers+text')
    )

    fig.update_layout(
        hoverdistance=10,
        hovermode='closest',
        clickmode='event+select',
        dragmode='pan'
    )

    return fig


def plot_country_publications(df):
    country_pubs = df['country'].value_counts().reset_index()
    country_pubs.columns = ['Country', 'Publications']
    
    # Calculate log scale for color mapping
    country_pubs['log_publications'] = np.log10(country_pubs['Publications'] + 1)
    
    fig = px.choropleth(country_pubs, 
                        locations='Country', 
                        locationmode='country names',
                        color='log_publications',
                        hover_name='Country',
                        hover_data={'Publications': True, 'log_publications': False},  
                        color_continuous_scale='Viridis',
                        title='Publications by Country')
    
    
    fig.update_layout(
        geo=dict(showframe=False, showcoastlines=True),
        coloraxis_colorbar=dict(
            title='Publications',
        )
    )
    
    return fig

def plot_citations_by_journal(df):
    journal_citations = df.groupby('journal').agg({'citations': 'sum', 'title': 'count'}).reset_index()
    journal_citations.columns = ['Journal', 'Total Citations', 'Number of Publications']
    journal_citations['Average Citations'] = journal_citations['Total Citations'] / journal_citations['Number of Publications']
    fig = px.scatter(journal_citations, x='Number of Publications', y='Total Citations',
                     size='Average Citations', color='Journal', hover_name='Journal',
                     log_x=True, log_y=True,
                     title='Journal Impact: Citations vs Publications')
    fig.update_layout(xaxis_title='Number of Publications (log scale)',
                      yaxis_title='Total Citations (log scale)')
    return fig

def plot_top_cited_papers(df):
    top_papers = df.nlargest(10, 'citations').copy()
    top_papers['short_title'] = top_papers['title'].str[:20] + "..."
    fig = px.bar(top_papers, x='citations', y='short_title', orientation='h',
             hover_data=['authors', 'year', 'journal'],
             title='Top 10 Most Cited Papers')
    fig.update_layout(yaxis={'categoryorder': 'total ascending'})
    return fig

def load_lottie_url(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()