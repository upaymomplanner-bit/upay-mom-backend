from fastapi import FastAPI
from app.routers import items

app = FastAPI(title="UPay MOM Backend", description="Backend for UPay MOM application")

app.include_router(items.router)


@app.get("/")
async def root():
    return {"message": "Welcome to UPay MOM Backend"}

