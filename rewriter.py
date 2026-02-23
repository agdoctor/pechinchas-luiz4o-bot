import google.genai as genai
from config import GEMINI_API_KEY
import asyncio
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
import re

# Configurar o cliente do Gemini (SDK novo)
if GEMINI_API_KEY:
    print(f"🔑 Chave Gemini carregada (Início: {GEMINI_API_KEY[:4]}...{GEMINI_API_KEY[-4:]})")
client = genai.Client(api_key=GEMINI_API_KEY)

# Modelo estável confirmado para esta conta específica
# Modelo estável (O usuário mostrou 2.5 no console, mas o SDK oficial costuma usar 1.5-flash ou 2.0-flash)
MODEL_ID = 'gemini-1.5-flash'

# Semaforo para evitar excesso de requisições simultâneas e garantir estabilidade
gemini_semaphore = asyncio.Semaphore(1)

def log_retry(retry_state):
    print(f"🔄 Tentativa {retry_state.attempt_number} de chamada ao Gemini falhou. Tentando novamente em {retry_state.next_action.sleep}s...")

PROMPT_SISTEMA = """
Você é o mestre das promoções do canal 'PECHINCHAS DO LUIZ4O'.
Sua tarefa é criar posts ENÉRGICOS, DIRETOS e IRRESISTÍVEIS!

REGRAS DE OURO:
1. SEJA RESUMIDO E DIRETO AO PONTO. O texto deve ser de fácil e rápida leitura.
2. USE UM TOM VIBRANTE E ENTUSIASTA! Use frases curtas de impacto como "PREÇO INVENCÍVEL!", "CORRE QUE VAI ACABAR!".
3. USE MUITO NEGRITO (<b>) para dar destaque aos nomes dos produtos e, principalmente, ao PREÇO.
4. PREÇOS: NUNCA INVENTE informações de preço. Se o texto original NÃO informar um preço "De:" (preço antigo/cheio), NÃO adicione essa formatação no texto final. Mostre apenas o preço atual da oferta.
5. USE EMOJIS variados para tornar o texto visualmente rico, mas evite exageros que poluam a leitura.
6. NUNCA mencione outros canais, grupos ou concorrentes. REMOVA qualquer link de terceiros ou nomes como 'nerdofertas'.
7. CUPOM COPIÁVEL E AZUL: SEMPRE que houver um cupom, você DEVE formatá-lo EXATAMENTE assim: `<a href="https://t.me/pechinchasdoluiz4o"><code>AQUI_O_CUPOM</code></a>`. ISSO É OBRIGATÓRIO! Exemplo: `Cupom: <a href="https://t.me/pechinchasdoluiz4o"><code>CELULAR10</code></a>`. Nunca deixe o cupom como texto puro.
8. NUNCA use a tag <br> ou <p>. Use quebras de linha reais estruturando bem os parágrafos.
9. PRESERVE OS LINKS INLINE: O texto original conterá marcações como [LINK_0], [LINK_1], etc. Você DEVE manter essas marcações EXATAMENTE onde elas estavam. Se estiver criando um texto DO ZERO, você DEVE terminar o corpo do texto com a marcação [LINK_0] para que o link de compra seja inserido.
10. NÃO termine o texto com emojis de carrinho ou setas de link, a menos que seja logo antes de um [LINK_X].

Retorne APENAS o HTML final. Seja épico e conciso!
"""

def limpar_emojis_finais(texto: str) -> str:
    """
    Remove emojis de call-to-action (carrinho, setas) que o Gemini teima em colocar no final
    para que não fiquem duplicados ou 'soltos' antes do link real.
    """
    # Remove espaços e quebras de linha no fim
    texto = texto.rstrip()
    # Regex para remover especificamente 🛒, 🖱️, ⬇️, 👉, 🔗 no final do texto
    texto = re.sub(r'[🛒🖱️⬇️👉🔗\s]+$', '', texto)
    return texto.strip()

@retry(
    wait=wait_exponential(multiplier=1, min=5, max=20),
    stop=stop_after_attempt(3),
    before_sleep=log_retry,
    reraise=True
)
async def _call_gemini_api(prompt: str) -> str:
    # Esta função interna permite o retry funcionar de verdade
    async with gemini_semaphore:
        response = await client.aio.models.generate_content(
            model=MODEL_ID,
            contents=prompt
        )
        # Pequeno intervalo para segurança
        await asyncio.sleep(1)
        return response.text.strip()

async def extrair_nome_produto(texto: str) -> str:
    """Extrai apenas o nome curto e principal do produto de um texto promocional usando o Gemini."""
    prompt = f"""
Extraia APENAS o nome do produto principal deste texto promocional.
Regras:
1. Retorne apenas o NOME do produto (ex: Smartphone Samsung Galaxy S25, Caixa de Som Tribit StormBox).
2. NÃO inclua adjetivos de promoção (ex: 'menor preço', 'promoção', 'barato').
3. NÃO inclua o preço.
4. Seja o mais breve e preciso possível (idealmente entre 2 a 6 palavras).
5. Se não houver produto claro, retorne exatamente o texto "Oferta Desconhecida".

Texto:
{texto}
"""
    try:
        resultado = await _call_gemini_api(prompt)
        nome = resultado.strip()
        # Fallback de segurança caso a IA ainda retorne um texto muito longo
        if len(nome.split()) > 15:
            nome = " ".join(nome.split()[:7])
        return nome
    except Exception as e:
        print(f"⚠️ Erro ao extrair nome do produto com Gemini: {e}")
        return ""


async def reescrever_promocao(texto_original: str) -> str:
    """
    Envia o texto original para o Gemini de forma assíncrona e retorna a versão reescrita.
    """
    try:
        prompt = f"{PROMPT_SISTEMA}\n\nTEXTO ORIGINAL:\n{texto_original}\n\nTEXTO REESCRITO:"
        reescrito = await _call_gemini_api(prompt)
        return limpar_emojis_finais(reescrito)
    except Exception as e:
        print(f"❌ Falha definitiva ao reescrever com Gemini após retries: {e}")
        return texto_original

async def gerar_promocao_por_link(titulo: str, link: str, preco: str, cupom: str, observacao: str = "") -> str:
    """
    Gera um texto de promoção do zero baseado nos dados scraped da URL e inputs manuais.
    """
    if not titulo:
        titulo = "Oferta Imperdível"
        
    cupom_str = f"Cupom de Desconto: {cupom} (LEMBRE-SE DA REGRA 7: Formate OBRIGATORIAMENTE este cupom como `<a href=\"https://t.me/pechinchasdoluiz4o\"><code>{cupom}</code></a>`)" if cupom and cupom.lower() not in ['não', 'nao', 'nenhum', '-'] else "Sem cupom específico."
    obs_str = f"- Observação Especial: {observacao}" if observacao else ""
    
    prompt = f"""
{PROMPT_SISTEMA}

INSTRUÇÃO ESPECIAL: Você não está reescrevendo um texto, está CRIANDO UM DO ZERO com essas informações de produto:
- Produto/Título Original: {titulo}
- Preço da Promoção: R$ {preco}
- {cupom_str}
{obs_str}

Crie um texto extremamente chamativo no padrão já estabelecido, destacando o preço de R$ {preco}. 
Se houver uma 'Observação Especial', incorpore-a de forma natural no texto (ex: se for 'Frete grátis', destaque isso).
SE PRECISAR REDUZIR o nome original do produto porque estava muito longo (padrão de lojas), FAÇA ISSO e deixe o nome dele limpo e natural.
NÃO coloque nenhum link dentro do texto que você gerar, o programa fará isso depois.
TEXTO GERADO:
"""
    try:
        gerado = await _call_gemini_api(prompt)
        return limpar_emojis_finais(gerado)
    except Exception as e:
        print(f"❌ Falha definitiva ao gerar texto com Gemini após retries: {e}")
        cupom_fallback_str = f"Cupom: <a href=\"https://t.me/pechinchasdoluiz4o\"><code>{cupom}</code></a>" if cupom and cupom.lower() not in ['não', 'nao', 'nenhum', '-'] else "Sem cupom específico."
        return f"🔥 **{titulo}**\n\n✅ Por Apenas R$ {preco}\n{cupom_fallback_str}" + (f"\n📝 {observacao}" if observacao else "")
