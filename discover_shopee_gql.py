import asyncio
import httpx
import json
import time
import hashlib
import os

# Mocking the configuration reading
# Credentials will be loaded from database
app_id = ""
app_secret = ""

async def discover_gql(item_id):
    fields = [
        "itemName", "productName", "item_name", "product_name", 
        "itemTitle", "productTitle", "title", "name",
        "imageUrl", "image_url"
    ]
    
    # We will try a few at a time or individually to see which one doesn't throw an error
    working_fields = []
    for field in fields:
        query = """
        query {
          productOfferV2(keyword: \"""" + str(item_id) + """\") {
            nodes {
              """ + field + """
            }
          }
        }
        """
        body = json.dumps({"query": query}, separators=(',', ':'))
        timestamp = int(time.time())
        base_str = f"{app_id}{timestamp}{body}{app_secret}"
        signature = hashlib.sha256(base_str.encode('utf-8')).hexdigest()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"SHA256 Credential={app_id}, Signature={signature}, Timestamp={timestamp}"
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post("https://open-api.affiliate.shopee.com.br/graphql", headers=headers, content=body)
                res_json = resp.json()
                if "errors" not in res_json:
                    print(f"[SUCCESS] Field '{field}' works!")
                    working_fields.append(field)
                else:
                    msg = res_json["errors"][0].get("message", "")
                    print(f"[FAIL] Field '{field}': {msg}")
        except Exception as e:
            print(f"[ERROR] Field '{field}': {e}")
            
    print(f"\nFinal working fields: {working_fields}")

if __name__ == "__main__":
    from database import get_config
    # Try to get actual config
    try:
        app_id = get_config("SHOPEE_APP_ID")
        app_secret = get_config("SHOPEE_APP_SECRET")
    except: pass
    
    asyncio.run(discover_gql("18999187340"))
