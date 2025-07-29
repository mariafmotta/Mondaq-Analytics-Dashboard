
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# Page configuration
st.set_page_config(page_title="Mondaq Analytics Dashboard", layout="wide")

# Title and summary
st.title("📊 Mondaq Analytics Dashboard")
st.markdown("""
Welcome to the Mondaq Analytics Dashboard. Use the filters in the sidebar to explore readership behavior, author performance, and article trends based on your audience data.
""")

# Load data
@st.cache_data
def load_data():
    reader_df = pd.read_csv("Reader-MondaqAnalytics.csv")
    article_df = pd.read_csv("Article-MondaqAnalytics.csv")
    author_df = pd.read_csv("Author-MondaqAnalytics.csv")

    reader_df.columns = reader_df.columns.str.strip()
    article_df.columns = article_df.columns.str.strip()
    author_df.columns = author_df.columns.str.strip()

    reader_df['Last Access Date'] = pd.to_datetime(reader_df['Last Access Date'], errors='coerce')
    article_df['Date'] = pd.to_datetime(article_df['Date'], errors='coerce')

    merged_df = article_df.merge(author_df, on='Author Id', how='left', suffixes=('_article', '_author'))
    merged_df = merged_df.rename(columns={'Reads_article': 'Article Reads', 'Author Name_article': 'Author Name'})

    return reader_df, article_df, author_df, merged_df

reader_df, article_df, author_df, merged_df = load_data()

# Sidebar filters
st.sidebar.header("📌 Filters")
country_filter = st.sidebar.selectbox("Filter by Country", ["All"] + sorted(reader_df['Country'].dropna().unique()))
industry_filter = st.sidebar.selectbox("Filter by Industry", ["All"] + sorted(reader_df['Industry'].dropna().unique()))

date_option = st.sidebar.selectbox("Select Time Window", ["All Time", "Last 7 Days", "Last 30 Days", "Last 90 Days"])
if date_option == "Last 7 Days":
    date_cutoff = datetime.now() - timedelta(days=7)
elif date_option == "Last 30 Days":
    date_cutoff = datetime.now() - timedelta(days=30)
elif date_option == "Last 90 Days":
    date_cutoff = datetime.now() - timedelta(days=90)
else:
    date_cutoff = None

# Apply filters
filtered_reader_df = reader_df.copy()
if country_filter != "All":
    filtered_reader_df = filtered_reader_df[filtered_reader_df["Country"] == country_filter]
if industry_filter != "All":
    filtered_reader_df = filtered_reader_df[filtered_reader_df["Industry"] == industry_filter]
if date_cutoff:
    filtered_reader_df = filtered_reader_df[filtered_reader_df["Last Access Date"] >= date_cutoff]

filtered_merged_df = merged_df.copy()
if date_cutoff:
    filtered_merged_df = filtered_merged_df[filtered_merged_df["Date"] >= date_cutoff]

# KPIs
col1, col2 = st.columns(2)
with col1:
    st.metric("Total Readers", value=f"{filtered_reader_df['Email'].nunique():,}")
with col2:
    st.metric("Total Reads", value=f"{filtered_reader_df['Reads'].sum():,}")

# Tabs
tab1, tab2, tab3 = st.tabs(["📈 Reader Insights", "📰 Article Insights", "✍️ Author Insights"])

# Tab 1 - Reader Insights
with tab1:
    st.subheader("Reader Job Profiles")
    st.bar_chart(filtered_reader_df['Position'].dropna().value_counts().nlargest(10))

    st.subheader("Access Source")
    if 'Activity Desc' in filtered_reader_df.columns:
        st.bar_chart(filtered_reader_df['Activity Desc'].value_counts())

    st.subheader("Readers by Country")
    country_counts = filtered_reader_df['Country'].value_counts().reset_index()
    country_counts.columns = ['Country', 'Count']
    fig_map = px.choropleth(country_counts, locations="Country", locationmode='country names', color="Count", title="Readers by Country")
    st.plotly_chart(fig_map, use_container_width=True)

# Tab 2 - Article Insights
with tab2:
    st.subheader("Top 5 Topics by Article Reads")
    topic_keywords = ['tax', 'esg', 'mergers', 'acquisition', 'privacy', 'compliance', 'digital', 'technology', 'employment']
    def match_topic(title):
        title = title.lower()
        for word in topic_keywords:
            if word in title:
                return word
        return 'other'
    topic_df = filtered_merged_df.copy()
    topic_df['Topic'] = topic_df['Title'].fillna('').apply(match_topic)
    top_topics = topic_df.groupby('Topic')['Article Reads'].sum().sort_values(ascending=False).head(5)
    fig_topics = px.bar(top_topics, x=top_topics.values, y=top_topics.index, orientation='h')
    st.plotly_chart(fig_topics, use_container_width=True)

    st.subheader("Common Search Terms (from Titles)")
    keywords = filtered_merged_df['Title'].dropna().str.lower().str.split().explode()
    clean_keywords = keywords[~keywords.isin(['the','and','for','with','from','this','that','will','how','can','are'])]
    top_keywords = clean_keywords.value_counts().nlargest(15)
    st.bar_chart(top_keywords)

    st.subheader("Top 5 Articles")
    top_articles = filtered_merged_df[['Title', 'Author Name', 'Article Reads', 'Date']].sort_values(by='Article Reads', ascending=False).head(5)
    for _, row in top_articles.iterrows():
        with st.container():
            st.markdown(f"**{row['Title']}**")
            st.markdown(f"📅 {row['Date'].date()} | ✍️ {row['Author Name']} | 🔢 Reads: {row['Article Reads']}")
            st.markdown("---")

# Tab 3 - Author Insights
with tab3:
    st.subheader("Top Authors by Total Reads")
    top_authors = filtered_merged_df.groupby('Author Name')['Article Reads'].sum().sort_values(ascending=False).head(10)
    fig = px.bar(top_authors, x=top_authors.values, y=top_authors.index, orientation='h', labels={'x': 'Total Reads', 'y': 'Author Name'})
    st.plotly_chart(fig, use_container_width=True)
