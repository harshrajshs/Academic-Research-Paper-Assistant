import streamlit as st
import requests

# Streamlit frontend
st.title("Academic Research Paper Assistant")

# Backend URL
BASE_URL = "http://127.0.0.1:8000"


# Fetch and store new papers for a topic
st.header("Fetch and Store New Papers")
fetch_topic = st.text_input("Enter a topic to fetch papers:")
if st.button("Fetch Papers"):
    response = requests.post(f"{BASE_URL}/fetch_and_store_papers", json={"topic": fetch_topic})
    if response.status_code == 200:
        data = response.json()
        st.success(data["status"])
        st.write("### Papers Added:")
        for paper in data.get("added_papers", []):
            st.write(f"- **{paper['title']}** ({paper['year']})")
    else:
        st.error(response.json().get("detail", "Error fetching papers"))


# Search papers
st.header("Search for Research Papers")
search_topic = st.text_input("Enter topic to search:")
start_year = st.number_input("Enter starting year:", min_value=2000, max_value=2024, value=2020)

if st.button("Search Papers"):
    response = requests.get(f"{BASE_URL}/get_papers", params={"topic": search_topic, "start_year": start_year})
    if response.status_code == 200:
        papers = response.json().get("papers", [])
        if papers:
            for paper in papers:
                st.subheader(paper.get("title", "No Title"))
                st.write(paper.get("abstract", "No Abstract"))
        else:
            st.info("No papers found.")
    else:
        st.error(response.json().get("detail", "Error searching papers."))


# Summarization
st.header("Summarize Research")
summarize_topic = st.text_input("Topic to summarize:")
if st.button("Summarize"):
    response = requests.post(f"{BASE_URL}/summarize", json={"topic": summarize_topic})
    if response.status_code == 200:
        st.write(response.json().get("summary"))
    else:
        st.error(response.json().get("detail", "Error summarizing research."))


# Future work suggestions
st.header("Future Research Suggestions")
suggest_topic = st.text_input("Topic for future research:")
if st.button("Get Suggestions"):
    response = requests.post(f"{BASE_URL}/future_works", json={"topic": suggest_topic})
    if response.status_code == 200:
        st.write(response.json().get("suggestions"))
    else:
        st.error(response.json().get("detail", "Error generating suggestions."))


# Question answering
st.header("Ask a Question")
qa_topic = st.text_input("Topic:")
question = st.text_input("Your question:")
if st.button("Ask Question"):
    response = requests.post(f"{BASE_URL}/qa", json={"topic": qa_topic, "question": question})
    if response.status_code == 200:
        similar_sentences = response.json().get("similar_sentences", [])
        for sent_data in similar_sentences:
            st.write(f"Sentence: {sent_data['sentence']}")
            st.write(f"Source: {sent_data['paper']['title']} ({sent_data['paper']['year']})")
            st.write(f"Similarity Score: {sent_data['similarity_score']:.2f}")
            st.write("---")
    else:
        st.error(response.json().get("detail", "Error answering question."))