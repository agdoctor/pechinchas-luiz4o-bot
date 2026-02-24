import asyncio
import affiliate
from config import AMAZON_TAG

async def test_amazon_conversion():
    print(f"Usando AMAZON_TAG: {AMAZON_TAG}")
    url = "https://www.amazon.com.br/Apple-iPhone-15-128-GB/dp/B0CP6CR795?th=1&linkCode=sl2&tag=garimposdodepinho-20&linkId=17f016f930f853d86b884c8bcc58ed90&ref_=as_li_ss_tl"
    
    converted = await affiliate.convert_to_affiliate(url)
    print(f"Original: {url}")
    print(f"Convertida: {converted}")
    
    assert AMAZON_TAG in converted
    assert "garimposdodepinho-20" not in converted
    assert "linkCode" not in converted
    
    print("\n✅ Conversão Amazon funcionando!")

if __name__ == "__main__":
    asyncio.run(test_amazon_conversion())
