import os
import json
from urllib import request, parse
from dotenv import load_dotenv
from config.log_config import setup_logger

load_dotenv(override=True)

logger = setup_logger()
GRAPH_API_URL = "https://graph.facebook.com"

PAGE_ID = os.getenv("FB_PAGE_ID")
ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")

def _post(url, data):
    encoded = parse.urlencode(data).encode()
    req = request.Request(url, data=encoded, method="POST")
    with request.urlopen(req) as resp:
        body = resp.read().decode()
        return json.loads(body)

def _upload_image_to_page(image_url):
    """Upload an image to the Facebook page without publishing it."""
    url = f"{GRAPH_API_URL}/{PAGE_ID}/photos"
    data = {
        "url": image_url,
        "published": "false",
        "access_token": ACCESS_TOKEN,
    }
    response = _post(url, data)
    media_id = response.get("id")
    logger.info(f"Image uploaded with media_fbid {media_id}")
    return media_id

def post_to_facebook_page(message, image_url=None):
    """Post a message to the Facebook page and return its post_id."""
    url = f"{GRAPH_API_URL}/{PAGE_ID}/feed"
    data = {
        "message": message,
        "access_token": ACCESS_TOKEN,
    }
    if image_url:
        media_id = _upload_image_to_page(image_url)
        data["attached_media[0]"] = json.dumps({"media_fbid": media_id})
    response = _post(url, data)
    post_id = response.get("id")
    logger.info(f"Post published with id {post_id}")
    return post_id

def cross_post_to_groups(post_id, group_ids):
    """Cross-post an existing page post to multiple Facebook groups."""
    results = []
    link = f"https://www.facebook.com/{post_id}"
    for gid in group_ids:
        url = f"{GRAPH_API_URL}/{gid}/feed"
        data = {
            "link": link,
            "access_token": ACCESS_TOKEN,
        }
        response = _post(url, data)
        gid_post_id = response.get("id")
        results.append(gid_post_id)
        logger.info(f"Post {post_id} shared to group {gid} as {gid_post_id}")
    return results
