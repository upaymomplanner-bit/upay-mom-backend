from fastapi import APIRouter

router = APIRouter(prefix="/items", tags=["items"])


@router.get("/")
async def read_items():
    return [{"item_id": 1, "name": "Item 1"}, {"item_id": 2, "name": "Item 2"}]


@router.get("/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id, "name": f"Item {item_id}"}