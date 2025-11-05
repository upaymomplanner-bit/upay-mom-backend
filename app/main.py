from fastapi import FastAPI
from app.routers import items
from app.routers.transcript import transcript_router

app = FastAPI(title="UPay MOM Backend", description="Backend for UPay MOM application")

app.include_router(items.router)
app.include_router(transcript_router)


@app.get("/")
async def root():
    return {"message": "Welcome to UPay MOM Backend"}
