import asyncio
from app.services.rate_limit_service import clear_login_failures

async def reset_all():
    phones = ["+263771000204", "+263771000001", "+263771000002", "+263771234567"]
    print(f"--- Clearing login failures for {len(phones)} key accounts ---")
    for phone in phones:
        await clear_login_failures(phone)
    print("Done.")

if __name__ == "__main__":
    asyncio.run(reset_all())
