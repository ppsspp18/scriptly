from fastapi import FastAPI

from routers.play_router import router as play_router
from routers.reader_router import router as reader_router

app = FastAPI(
    title="Scriptly API",
    version="1.0.0"
)

app.include_router(play_router)
app.include_router(reader_router)


@app.get("/")
def root():
    return {
        "message": "Scriptly API Running"
    }
