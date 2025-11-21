from substack_api import Post, Newsletter, User
from typing import List
from datetime import datetime, timezone
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_substack_posts(username: str, date: str) -> dict:
    """Downloads posts from all newsletters that a user is subscribed to within a given time range.

    Args:
        username (str): The username of the user to download posts for
        date (str): The date to download posts from in the format %Y-%m-%dT%H:%M:%S.%f%z

    Returns:
        Dictionary containing the status of the download and a message describing the result.
        Success: {"status": "success", "message": "Posts downloaded successfully"}
        Error: {"status": "error", "message": "Error downloading posts"}
    """

    user = User(username)
    newsletters = {}
    for d in user.get_subscriptions():
        try:
            newsletters[d["publication_name"]] = Newsletter(f"https://{d["domain"]}")
            logging.info(f"Added newsletter: {d['publication_name']}")
        except Exception as e:
            logging.error(f"Error adding newsletter {d['publication_name']}: {e}")
            continue
    
    for name, newsletter in newsletters.items():
        response = get_posts_by_newsletter(newsletter, name, date)
        if response["status"] == "error":
            return response
    return {"status": "success", "message": "Posts downloaded successfully"}
    
    
def get_posts_by_newsletter(newsletter: Newsletter, name: str, date: str) -> dict:
    """Downloads posts from a newsletter within a given time range.

    Args:
        newsletter (Newsletter): The newsletter to download posts from
        name (str): The name of the newsletter
        date (str): The date to download posts from in the format %Y-%m-%dT%H:%M:%S.%f%z

    Returns:
        Dictionary containing the status of the download and a message describing the result.
        Success: {"status": "success", "message": "Posts downloaded successfully"}
        Error: {"status": "error", "message": "Error downloading posts"}
    """

    dt = datetime.strptime(date,  "%Y-%m-%dT%H:%M:%S.%f%z")
    # Get the number of posts equal to number of days from the given date to today
    days = datetime.now(timezone.utc) - dt
    days = days.days

    try:
        posts = newsletter.get_posts(sorting='new', limit=days)

        filtered_posts = get_posts_after_date(posts, dt)

        for post in filtered_posts:
            try:
                metadata = post.get_metadata()
                content = post.get_content()
                Path(f'post_content/{name}').mkdir(parents=True, exist_ok=True)
                with open(f"post_content/{name}/{metadata["slug"]}.html", 'w') as f:
                    f.write(content)
                logging.info(f"Added post {metadata['slug']} from newsletter {name}")
            except Exception as e:
                logging.error(f"Error adding post {metadata['slug']} from newsletter {name}: {e}")
                continue
        
        return {"status": "success", "message": "Posts downloaded successfully"}
    
    except Exception as e:
        logging.error(f"Error downloading posts from newsletter {name}: {e}")
        return {"status": "error", "message": str(e)}


def get_posts_after_date(posts: List[Post], dt: datetime) -> List[Post]:
    """Filter posts to only include those published after a given date.

    Args:
        posts : List[Post]
            List of posts to filter
        dt : datetime
            Date to filter by

    Returns:
        List[Post]
            List of posts published after the given date
    """
    res = []
    for post in posts:
        post_date = datetime.strptime(post.get_metadata()["post_date"], "%Y-%m-%dT%H:%M:%S.%f%z")
        if post_date >= dt:
            res.append(post)
    return res