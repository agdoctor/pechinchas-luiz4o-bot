# 🔍 Análise de Concorrentes Diretos: SaaS Afiliado

Esta análise compara o seu futuro SaaS com as três principais ferramentas do mercado brasileiro voltadas diretamente para afiliados: **Divulgador Inteligente (também conhecido como Afiliado Inteligente)** e **Promospot.ai**.

---

## 🆚 1. Divulgador Inteligente (Afiliado Inteligente)
*Nota: "Afiliado Inteligente" é o nome popular orgânico que o mercado dá, mas o software comercialmente se chama "Divulgador Inteligente".*

### Como Funciona:
É basicamente um Bot de Telegram bem polido. Você manda um link cru da Amazon no chat privado deles, e o bot devolve o link encurtado (com o ID de afiliado) e uma arte com o preço gerada num template de Instagram.

### 🎯 Pontos Fortes:
*   **Gerador de Imagens Integrado:** O maior diferencial deles. Recebem a foto principal da Amazon e já colam num fundo temático para Instagram Stories com o preço em texto por cima.
*   **Integração Nativa de Redes (Deeplink):** Conectam com muitas contas: Shopee, Amz, Magalu, AliExpress, Awin, etc.
*   **Site de Vitrine:** Planos mais caros geram um site "mini-ecommerce" com as ofertas que o afiliado encurtou.

### 💸 Preços Atuais:
*   **Essencial (R$ 67/mês):** Limitado. Geralmente focado só em Magalu e Shopee.
*   **Ouro (R$ 137/mês):** Libera Amazon, AliExpress e outras redes.
*   **Diamante (R$ 189/mês):** Libera o "Cofre de Promoções" avançado (um site próprio com domínio).

### 🚨 Onde o Seu SaaS Ganha Deles:
*   **Zero Automação Real de Disparo:** O Divulgador Inteligente é apenas um *conversor e criador de artes*. O afiliado tem que estar acordado 24h, pegar cada link, enviar pro bot deles, copiar o resultado e ele *mesmo* enviar pro grupo de clientes.
*   **A "Máquina de Renda Passiva":** O **SEU** bot monitora a concorrência e atira pro grupo automaticamente. O Divulgador Inteligente não faz o trabalho braçal da postagem.

---

## 🆚 2. Promospot.ai
### Como Funciona:
É a plataforma que mais se aproxima da sua ideia de negócio (um grande competidor). É um misto de Extensão no Chrome com um SaaS de Automação de WhatsApp/Telegram.

### 🎯 Pontos Fortes:
*   **Smart Redirector (Encaminhamento Inteligente):** Eles resolvem o problema de limite de whatsapp. Se o link for `promospot.com/zap` e o grupo 1 lotar, eles jogam pro grupo 2 automaticamente. (Isso é similar ao que a Conecta Tribo faz, mas nativo).
*   **Interface Extensão do Chrome:** Quando o afiliado está navegando na Amazon no computador, ele clica num botão no Google Chrome e a oferta já vai pro grupo na hora gerado por IA.

### 💸 Preços Atuais:
*   Geralmente cobram de R$ 97 a R$ 297/mês dependendo dos tetos de disparo e quantidade de grupos.

### 🚨 Onde o Seu SaaS Ganha Deles:
*   **Copywriting Rígido vs Personalidade IA:** O Promospot monta textos estruturados de IA muito parecidos com "padrão mercado". No seu bot, nós montamos uma estrutura de prompt onde o usuário pode colocar "Destaque mais o Humor e Escassez".
*   **O Diferencial Monitor de Canais:** O Promospot ajuda muito o afiliado a **enviar** coisas que ele acha. O seu bot **garimpa sozinho** dos canais ocultos (ex: @promotop) via Telegram Core API e já rouba a oferta pro cliente. Essa é a funcionalidade *Matadora* do seu robô.

---

## 💡 Como Extrair as Melhores Ideias Deles Para o Seu Negócio?

Para garantir que o seu plano **Pro (R$ 497)** pareça barato, nós podemos "roubar artisticamente" essas funcionalidades nos próximos meses:

1. **A Função da Extensão de Chrome (Inspirado no Promospot)**
   *   Muitos que garimpam não querem ficar caçando oferta em celular. No futuro, criar uma extensão fuleira do Chrome onde o cliente clica "Gerar Bot" na página da Amazon seria bizarro de bom.
2. **"Arte" Gerada na Hora (Inspirado no Divulgador Inteligente)**
   *   O nosso robô baixa a foto da Amazon com fundo branco. Nós podemos rodar um código em *Pillow* (Biblioteca Python que usamos na marca d'água) para em vez de só botar logo, colocar a foto do produto em cima de um "Card Bonito" com o PREÇO da IA colado na foto em texto gigante, pronto pra virar Story de Instagram do cliente.
3. **O Link de Bio (Inspirado no Promospot e Linktree)**
   *   Criar uma página com a nossa dashboard que em vez de ser painel, exibe para o cliente *final* (dona de casa) uma listinha bonitinha das 10 últimas ofertas que o bot achou. É super fácil de fazer usando o banco de dados atual!
