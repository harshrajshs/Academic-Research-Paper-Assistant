from neo4j import GraphDatabase

class Neo4jHelper:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def add_paper(self, title, year, abstract):
        """
        Adds a paper to the Neo4j database.
        """
        with self.driver.session() as session:
            session.run(
                """
                CREATE (p:Paper {title: $title, year: $year, abstract: $abstract})
                """, 
                title=title, year=year, abstract=abstract
            )

    def query_papers_by_year(self, topic, start_year):
        """
        Queries papers by a specific topic and starting year.
        """
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (p:Paper)
                WHERE p.year >= $start_year AND 
                    (toLower(p.title) CONTAINS toLower($topic) OR 
                    toLower(p.abstract) CONTAINS toLower($topic))
                RETURN p.title AS title, p.abstract AS abstract, p.year AS year
                """, 
                topic=topic, start_year=start_year
            )
            return [
                {"title": record["title"], "abstract": record["abstract"], "year": record["year"]}
                for record in result
            ]


    def query_papers_by_topic(self, topic):
        """
        Queries papers by a specific topic, regardless of the year.
        """
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (p:Paper)
                WHERE toLower(p.title) CONTAINS toLower($topic) OR 
                    toLower(p.abstract) CONTAINS toLower($topic)
                RETURN p.title AS title, p.abstract AS abstract, p.year AS year
                """, 
                topic=topic
            )
            return [
                {"title": record["title"], "abstract": record["abstract"], "year": record["year"]}
                for record in result
            ]


    def delete_paper_by_title(self, title):
        """
        Deletes a paper from the database by its title.
        """
        with self.driver.session() as session:
            session.run(
                """
                MATCH (p:Paper {title: $title})
                DETACH DELETE p
                """, 
                title=title
            )

    def update_paper(self, title, new_data):
        """
        Updates a paper's properties in the database.
        """
        with self.driver.session() as session:
            session.run(
                """
                MATCH (p:Paper {title: $title})
                SET p += $new_data
                """, 
                title=title, new_data=new_data
            )

    def get_all_papers(self):
        """
        Retrieves all papers from the database.
        """
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (p:Paper)
                RETURN p.title AS title, p.abstract AS abstract, p.year AS year
                """
            )
            return [
                {"title": record["title"], "abstract": record["abstract"], "year": record["year"]}
                for record in result
            ]
