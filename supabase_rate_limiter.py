from supabase import create_client
from datetime import datetime
import os

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
LIMIT = 20

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_remaining_calls(email):
    res = supabase.table("usage_logs").select("*").eq("email", email).execute()
    if res.data:
        used = res.data[0].get("count", 0)
        return max(0, LIMIT - used)
    return LIMIT

def check_and_increment_usage(email):
    response = supabase.table("usage_logs").select("*").eq("email", email).execute()
    if response.data:
        user = response.data[0]
        count = user["count"]
        if count >= LIMIT:
            raise Exception(f"You’ve hit your usage limit of {LIMIT} calls.")
        # increment count
        supabase.table("usage_logs").update({
            "count": count + 1,
            "updated_at": datetime.now().isoformat()
        }).eq("email", email).execute()
    else:
        # First time user
        supabase.table("usage_logs").insert({
            "email": email,
            "count": 1,
            "updated_at": datetime.now().isoformat()
        }).execute()
