import openai
from fastapi import FastAPI, HTTPException, Body
from neo4j_helper import Neo4jHelper
from search_agent import SearchAgent
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
import requests

nltk.download('punkt')  # Ensure NLTK is set up for tokenization

# Initialize FastAPI app
app = FastAPI()

# Initialize search agent and Neo4j connection
search_agent = SearchAgent()
db = Neo4jHelper("neo4j://localhost:7687", "neo4j", "1qw23er4")


def find_most_similar_sentences(question, papers, top_k=5):
    """
    Finds the most similar sentences to the given question using TF-IDF vectorization.
    """
    # Combine paper titles and abstracts into a list of sentences
    sentences = []
    paper_mapping = []
    for paper in papers:
        title = paper.get("title", "Unknown Title")
        abstract = paper.get("abstract", "")
        if title:
            sentences.append(title)
            paper_mapping.append(paper)
        if abstract:
            sentences.append(abstract)
            paper_mapping.append(paper)

    # Vectorize the question and sentences using TF-IDF
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([question] + sentences)  # First row is the question
    question_vector = tfidf_matrix[0:1]
    sentence_vectors = tfidf_matrix[1:]

    # Compute cosine similarity
    similarities = cosine_similarity(question_vector, sentence_vectors).flatten()

    # Get top-k most similar sentences
    top_indices = similarities.argsort()[-top_k:][::-1]
    most_similar_sentences = [(sentences[i], paper_mapping[i], similarities[i]) for i in top_indices]

    return most_similar_sentences


def fetch_papers_from_arxiv(topic, max_results=5):
    """
    Fetches papers from arXiv based on the topic.
    """
    try:
        base_url = "http://export.arxiv.org/api/query"
        query = f"search_query=all:{topic}&start=0&max_results={max_results}&sortBy=relevance&sortOrder=descending"
        response = requests.get(f"{base_url}?{query}")
        
        if response.status_code != 200:
            raise Exception("Error fetching data from arXiv API.")

        # Parse response
        from xml.etree import ElementTree as ET
        root = ET.fromstring(response.content)
        papers = []
        for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
            title = entry.find("{http://www.w3.org/2005/Atom}title").text.strip()
            summary = entry.find("{http://www.w3.org/2005/Atom}summary").text.strip()
            published_date = entry.find("{http://www.w3.org/2005/Atom}published").text.strip()[:4]
            
            papers.append({"title": title, "abstract": summary, "year": published_date})
        
        return papers
    except Exception as e:
        raise Exception(f"Failed to fetch papers: {e}")


@app.post("/fetch_and_store_papers")
def fetch_and_store_papers(topic: str = Body(..., embed=True)):
    try:
        # Fetch top 5 papers from arXiv
        papers = fetch_papers_from_arxiv(topic, max_results=5)
        
        if not papers:
            return {"status": f"No papers found on '{topic}'."}
        
        # Store papers in the database and keep track of added papers
        added_papers = []
        for paper in papers:
            db.add_paper(title=paper["title"], year=int(paper["year"]), abstract=paper["abstract"])
            added_papers.append({"title": paper["title"], "year": paper["year"]})
        
        return {
            "status": f"Top {len(added_papers)} papers on '{topic}' fetched and stored successfully.",
            "added_papers": added_papers,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")



@app.get("/get_papers")
def get_papers(topic: str, start_year: int):
    """
    Retrieves papers based on a topic and starting year.
    """
    try:
        # Fetch papers from the database
        papers = db.query_papers_by_year(topic, start_year)
        if not papers:
            return {"message": f"No papers found on topic '{topic}' after year {start_year}."}
        
        # Return the list of papers
        return {"papers": papers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")



@app.post("/summarize")
def summarize(topic: str = Body(..., embed=True)):
    try:
        papers = db.query_papers_by_topic(topic)
        summaries = [paper.get("abstract", "No abstract available") for paper in papers]
        return {"summary": " ".join(summaries[:5])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


@app.post("/future_works")
def future_works(topic: str = Body(..., embed=True)):
    try:
        papers = db.query_papers_by_topic(topic)
        gaps = [f"Paper: {paper['title']}, Abstract: {paper.get('abstract', '')[:200]}..." for paper in papers[:5]]
        suggestions = "Based on research, here are potential gaps:\n" + "\n".join(gaps)
        return {"suggestions": suggestions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


@app.post("/qa")
def qa(topic: str = Body(..., embed=True), question: str = Body(..., embed=True)):
    try:
        papers = db.query_papers_by_topic(topic)
        similar_sentences = find_most_similar_sentences(question, papers)

        response = {
            "question": question,
            "topic": topic,
            "similar_sentences": [
                {
                    "sentence": sent,
                    "paper": {"title": paper.get("title"), "year": paper.get("year")},
                    "similarity_score": score,
                }
                for sent, paper, score in similar_sentences
            ],
        }
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
