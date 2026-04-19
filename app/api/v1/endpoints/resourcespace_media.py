import hashlib
import requests
from fastapi import APIRouter

router = APIRouter()

PRIVATE_KEY = "1fbbd031191aa09570453f06e0b20d0b2556765899b57363164a8ef32a236072"
USER = "admin"
BASE_URL = "http://172.31.10.53/resourcespace/api/"


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
            "title": res.get("field8") or res.get("name"),  # adjust if needed
        })

    return {
        "status": "success",
        "data": formatted
    }