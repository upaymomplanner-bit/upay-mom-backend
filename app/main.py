from fastapi import FastAPI, Request, HTTPException
from app.services.auth.deps import get_supabase_client
from app.routers import items
from app.routers.transcript import transcript_router

app = FastAPI(title="UPay MOM Backend", description="Backend for UPay MOM application")

app.include_router(items.router)
app.include_router(transcript_router)


@app.get("/")
async def root():
    return {"message": "Welcome to UPay MOM Backend"}


@app.middleware("http")
async def supabase_auth_middleware(
    request: Request,
    call_next,
):
    if request.method == "OPTIONS":
        return await call_next(request)

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")

    jwt_token = auth_header.split(" ")[1]
    supabase = await get_supabase_client()
    user = await supabase.auth.get_user(jwt_token)
    if not user or not user.user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    response = await call_next(request)
    return response
