# search_agent.py
import arxiv
from neo4j_helper import Neo4jHelper

class SearchAgent:
    def __init__(self):
        self.db = Neo4jHelper("neo4j://localhost:7687", "neo4j", "1qw23er4")

    def fetch_and_store_papers(self, topic):
        search = arxiv.Search(query=topic, max_results=5, sort_by=arxiv.SortCriterion.SubmittedDate)
        for result in search.results():
            self.db.add_paper(result.title, result.published.year, result.summary)