import hashlib
import requests
import logging  # Changed: import logging from Python standard library
from fastapi import APIRouter, HTTPException, Query

router = APIRouter()
logger = logging.getLogger(__name__)

PRIVATE_KEY = "691527108155802fad51a2b4dd8f26e943d4b231ff6747101a2603e6780870f4"
USER = "admin"
BASE_URL = "http://172.16.9.132/resourcespace/api/"


def generate_signature(query: str):
    return hashlib.sha256((PRIVATE_KEY + query).encode()).hexdigest()


@router.get("/")
def get_resources():
    """
    Lightweight API → returns only basic resource info
    """

    query = f"user={USER}&function=do_search&search="
    sign = generate_signature(query)

    response = requests.get(f"{BASE_URL}?{query}&sign={sign}")
    resources = response.json()

    if not isinstance(resources, list):
        return {"status": "success", "data": []}

    formatted = []

    for res in resources:
        formatted.append({
            "id": res.get("ref"),
            "title": res.get("field8") or res.get("name"),
            "creation_date": res.get("creation_date")
        })

    return {
        "status": "success",
        "data": formatted
    }


@router.get("/by-title/")
def get_resources_by_title(
    title: str = Query(..., description="Title to search for")
):
    """
    Fetch resource IDs based on a given title.
    
    Args:
        title: Title to search for
    
    Returns:
        List of resources matching the title
    """
    
    # Try multiple search approaches
    
    # Approach 1: Standard partial match on field8
    search_query = f"field8:{title}"
    query = f"user={USER}&function=do_search&search={search_query}"
    sign = generate_signature(query)
    
    try:
        response = requests.get(f"{BASE_URL}?{query}&sign={sign}", timeout=30)
        response.raise_for_status()
        resources = response.json()
        
        # Log the response for debugging
        logger.info(f"Search query: {search_query}")
        logger.info(f"Response type: {type(resources)}")
        logger.info(f"Response content: {resources}")
        
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching from ResourceSpace API: {str(e)}")
    except ValueError as e:
        raise HTTPException(status_code=500, detail=f"Error parsing ResourceSpace response: {str(e)}")
    
    # If no results found with field8, try searching in all fields
    if not isinstance(resources, list) or len(resources) == 0:
        # Approach 2: Search in all fields using asterisk
        search_query = f"*:{title}"
        query = f"user={USER}&function=do_search&search={search_query}"
        sign = generate_signature(query)
        
        try:
            response = requests.get(f"{BASE_URL}?{query}&sign={sign}", timeout=30)
            response.raise_for_status()
            resources = response.json()
            logger.info(f"Fallback search query: {search_query}")
        except:
            pass
    
    # If still no results, try to fetch all resources and filter locally
    if not isinstance(resources, list) or len(resources) == 0:
        # Approach 3: Get all resources and filter
        query = f"user={USER}&function=do_search&search="
        sign = generate_signature(query)
        
        try:
            response = requests.get(f"{BASE_URL}?{query}&sign={sign}", timeout=30)
            response.raise_for_status()
            all_resources = response.json()
            
            if isinstance(all_resources, list):
                # Filter resources where title matches (case-insensitive partial match)
                resources = [
                    res for res in all_resources 
                    if title.lower() in (res.get("field8") or res.get("name") or "").lower()
                ]
                logger.info(f"Found {len(resources)} resources via local filtering")
        except:
            pass
    
    if not isinstance(resources, list) or len(resources) == 0:
        return {
            "status": "success", 
            "data": [], 
            "message": f"No resources found with title: {title}",
            "debug_info": {
                "searched_title": title,
                "note": "Try checking field mapping in ResourceSpace"
            }
        }
    
    formatted = []
    for res in resources:
        formatted.append({
            "id": res.get("ref"),
            "title": res.get("field8") or res.get("name"),
            "creation_date": res.get("creation_date")
        })
    
    return {
        "status": "success",
        "count": len(formatted),
        "data": formatted
    }


