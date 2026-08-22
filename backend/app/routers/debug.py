@router.get("/debug/db-url")
async def debug_db_url():
    from app.config import settings
    url = settings.database_url
    if "proxy.rlwy.net" in url:
        return {"network": "public", "host": url.split("@")[1].split("/")[0]}
    else:
        return {"network": "private", "host": url.split("@")[1].split("/")[0]}
