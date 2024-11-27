import requests
from dotenv import load_dotenv
import os
from openai import OpenAI
from neo4j import GraphDatabase

from utils import post_json_data_to_url


load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_PROJECT_ID = os.getenv("OPENAI_PROJECT_ID")
OPENAI_ORGANIZATION_ID = os.getenv("OPENAI_ORGANIZATION_ID")
CENTRALA_BASE_URL = os.getenv("CENTRALA_BASE_URL")
AIDEVS_MY_APIKEY = os.getenv("AIDEVS_MY_APIKEY")
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASS = os.getenv("NEO4J_PASS")

openai_client = OpenAI(
    organization=OPENAI_ORGANIZATION_ID,
    project=OPENAI_PROJECT_ID,
    api_key=OPENAI_API_KEY,
)


def get_response_from_url(url, input_json):
    response = requests.get(url, json=input_json)
    return response.json()


def query_structure(sql_query_text):
    return {
        "task": "database",
        "apikey": AIDEVS_MY_APIKEY,
        "query": sql_query_text
}


def load_users_to_neo4j(uri, auth, users):
    """Load users data into Neo4j database as User nodes.
    
    Args:
        uri (str): Neo4j connection URI
        auth (tuple): Authentication credentials (username, password)
        users (list): List of user dictionaries
    """
    def create_user_node(tx, user):
        # Convert string values to appropriate types
        is_active = user['is_active'] == '1'
        
        query = """
        MERGE (u:User {id: $id})
        SET u.username = $username,
            u.access_level = $access_level,
            u.is_active = $is_active,
            u.lastlog = date($lastlog)
        """
        tx.run(query, 
            id=user['id'],
            username=user['username'],
            access_level=user['access_level'],
            is_active=is_active,
            lastlog=user['lastlog']
        )

    try:
        with GraphDatabase.driver(uri, auth=auth) as driver:
            with driver.session() as session:
                for user in users:
                    session.execute_write(create_user_node, user)
                print(f"Successfully loaded {len(users)} users into Neo4j")
    except Exception as e:
        print(f"Error loading users into Neo4j: {str(e)}")


def load_connections_to_neo4j(uri, auth, connections):
    """Load connections data into Neo4j database as KNOWS relationships between User nodes.
    
    Args:
        uri (str): Neo4j connection URI
        auth (tuple): Authentication credentials (username, password)
        connections (list): List of connection dictionaries with user1_id and user2_id
    """
    def create_connection(tx, from_id, to_id):
        query = """
        MATCH (u1:User {id: $from_id})
        MATCH (u2:User {id: $to_id})
        MERGE (u1)-[r:KNOWS]->(u2)
        """
        tx.run(query, from_id=from_id, to_id=to_id)

    try:
        with GraphDatabase.driver(uri, auth=auth) as driver:
            with driver.session() as session:
                for connection in connections:
                    session.execute_write(
                        create_connection, 
                        connection['user1_id'], 
                        connection['user2_id']
                    )
                print(f"Successfully loaded {len(connections)} connections into Neo4j")
    except Exception as e:
        print(f"Error loading connections into Neo4j: {str(e)}")



def find_shortest_path(uri, auth, from_username, to_username):
    """Find shortest path between two users and return list of usernames.
    
    Args:
        uri (str): Neo4j connection URI
        auth (tuple): Authentication credentials (username, password)
        from_username (str): Starting user's username
        to_username (str): Target user's username
        
    Returns:
        list: List of usernames representing the path, or empty list if no path exists
    """
    def get_path(tx, from_user, to_user):
        query = """
        MATCH path = shortestPath(
            (start:User {username: $from_user})-[:KNOWS*]-(end:User {username: $to_user})
        )
        RETURN [node in nodes(path) | node.username] as path
        """
        result = tx.run(query, from_user=from_user, to_user=to_user)
        record = result.single()
        return record["path"] if record else []

    try:
        with GraphDatabase.driver(uri, auth=auth) as driver:
            with driver.session() as session:
                path = session.execute_read(get_path, from_username, to_username)
                return path
    except Exception as e:
        print(f"Error finding path: {str(e)}")
        return []


if __name__ == "__main__":
    users = get_response_from_url(
        f"{CENTRALA_BASE_URL}/apidb",
        query_structure("select * from users ")
    )["reply"]

    connections = get_response_from_url(
        f"{CENTRALA_BASE_URL}/apidb",
        query_structure("select * from connections ")
    )["reply"]

    print(users)
    print(connections)
    load_users_to_neo4j(NEO4J_URI, (NEO4J_USER, NEO4J_PASS), users)
    load_connections_to_neo4j(NEO4J_URI, (NEO4J_USER, NEO4J_PASS), connections)
    path = find_shortest_path(NEO4J_URI, (NEO4J_USER, NEO4J_PASS), "Rafał", "Barbara")
    print(path)

    payload = {
        "task": "connections",
        "apikey": AIDEVS_MY_APIKEY,
        "answer": ", ".join(path)
    }
    print(f"payload: {payload}")
    post_json_data_to_url(payload, f"{CENTRALA_BASE_URL}/report")
