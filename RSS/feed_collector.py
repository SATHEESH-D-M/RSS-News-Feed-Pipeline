import os
import time
import requests
import psycopg2
from typing import Optional, List
import psycopg2.extensions
import feedparser
import base64
from io import BytesIO
import logging

# Database configuration
DB_NAME = os.getenv("POSTGRES_DB", "news_db")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")

# RSS feed and field mappings
RSS_FEED_URL = os.getenv("RSS_FEED_URL", "https://www.thehindu.com/feeder/default.rss")
TITLE_PATH = os.getenv("TITLE_PATH", "title")
TIMESTAMP_PATH = os.getenv("TIMESTAMP_PATH", "published")
WEBLINK_PATH = os.getenv("WEBLINK_PATH", "link")
IMAGE_PATH = os.getenv("IMAGE_PATH", "media_content")
IMAGE_URL_PATH = os.getenv("IMAGE_URL_PATH", "url")
SUMMARY_PATH = os.getenv("SUMMARY_PATH", "summary")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "600"))

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def get_db_connection():
    """
    Establish a connection to the PostgreSQL database.

    Returns:
        conn (psycopg2.extensions.connection or None):
            The PostgreSQL database connection object if successful,
            or None if the connection fails.

    Environment Variables:
        DB_NAME (str): The name of the PostgreSQL database.
        DB_USER (str): The username for database authentication.
        DB_PASSWORD (str): The password for database authentication.
        DB_HOST (str): The hostname or IP address of the database server.
        DB_PORT (str, optional): The port number to connect to the database (default: "5432").

    Error Handling:
        Catches psycopg2.Error and logs the error message without crashing the program.

    Example:
        conn = get_db_connection()
        if conn:
            print("Connected to the database")
    """
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
        )
        logging.info("Database connection successful.")
        return conn
    except psycopg2.Error as e:
        logging.error(f"Database connection failed: {e}")
        return None


def fetch_and_encode_image(img_url: str) -> Optional[str]:
    """
    Fetch an image from the given URL and convert it to a base64-encoded string.

    Args:
        img_url (str): The URL of the image to be fetched.

    Returns:
        Optional[str]: Base64-encoded string of the image if successful, None otherwise.
    """
    try:
        response = requests.get(img_url)
        if response.status_code == 200:
            img_data = BytesIO(response.content)
            return base64.b64encode(img_data.read()).decode("utf-8")
        else:
            logging.error(f"Failed to fetch image, HTTP Status: {response.status_code}")
            return None
    except Exception as e:
        logging.error(f"Failed to fetch image: {e}")
        return None


def parse_tags(tags: Optional[List[dict]]) -> List[str]:
    """
    Parse tags from a list of dictionaries, extracting all non-empty values
    regardless of the keys, and return them as a list of strings.

    Args:
        tags (Optional[List[dict]]): A list of dictionaries containing tag data.
                                     Each dictionary may have arbitrary keys.

    Returns:
        List[str]: A list of all non-empty tag values as strings.
    """
    if not tags:
        return []
    return [str(value) for tag in tags for value in tag.values() if value]


def insert_article(
    conn: psycopg2.extensions.connection,
    title: str,
    publication_timestamp: Optional[str],
    weblink: str,
    picture: Optional[bytes],
    tags: List[str],
    summary: Optional[str],
) -> None:
    """
    Insert a new article into the news_articles table.
    If an article with the same title and publication timestamp already exists, do nothing.

    Args:
        conn (psycopg2.extensions.connection): The PostgreSQL database connection.
        title (str): The title of the article.
        publication_timestamp (Optional[str]): The publication timestamp of the article.
        weblink (str): The link to the full article.
        picture (Optional[bytes]): The base64-encoded image of the article.
        tags (List[str]): A list of tags associated with the article.
        summary (Optional[str]): A brief summary of the article.

    Returns:
        None
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO news_articles (title, publication_timestamp, weblink, picture, tags, summary)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (title, publication_timestamp) DO NOTHING;
            """,
            (title, publication_timestamp, weblink, picture, tags, summary),
        )
        conn.commit()


def fetch_feed() -> None:
    """
    Parse the RSS feed and insert each article into the database.

    Iterates through the entries in the RSS feed, extracts relevant fields,
    processes the image, and inserts the data into the news_articles table.

    Returns:
        None
    """
    feed = feedparser.parse(RSS_FEED_URL)
    conn = get_db_connection()
    if not conn:
        logging.error("Skipping feed processing due to database connection failure.")
        return

    try:
        for entry in feed.entries:
            title = entry.get(TITLE_PATH, "")
            publication_timestamp = entry.get(TIMESTAMP_PATH, "")
            weblink = entry.get(WEBLINK_PATH, "")
            image_url = entry.get(IMAGE_PATH, [{}])[0].get(IMAGE_URL_PATH, "") if entry.get(IMAGE_PATH) else ""
            picture = fetch_and_encode_image(image_url)
            tags = parse_tags(entry.get("tags", []))
            summary = entry.get(SUMMARY_PATH, "")
            insert_article(conn, title, publication_timestamp, weblink, picture, tags, summary)
    finally:
        conn.close()


def main() -> None:
    """
    Continuously poll the RSS feed at regular intervals.

    Fetches the RSS feed, processes the articles, and sleeps for the specified
    polling interval before repeating the process.

    Returns:
        None
    """
    while True:
        # initial wait for the db container to start the db
        time.sleep(10)

        # fetch and feed
        logging.info("Fetching RSS feed...")
        fetch_feed()
        logging.info(f"Sleeping for {POLL_INTERVAL} seconds...")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
