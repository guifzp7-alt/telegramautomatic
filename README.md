# Telegram Disparador

Painel web responsivo para montar e disparar publicações pelo Telegram Bot API.

## O que faz
- Texto/legenda
- Várias fotos em álbum
- Vídeo único
- Botão com texto + link
- Prévia no navegador
- Histórico simples dos últimos disparos
- Login Basic Auth
- Compatível com Render Free como Web Service

## Antes de publicar no Render
1. Crie um bot no @BotFather e copie o BOT TOKEN.
2. Adicione o bot ao canal/grupo de destino.
3. Dê ao bot permissão para publicar/enviar mensagens.
4. Descubra o `TARGET_CHAT_ID` do canal/grupo. Para canais, normalmente é um ID começando por `-100`.
5. Configure as variáveis de ambiente.

## Render
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:app --bind 0.0.0.0:$PORT`

### Variáveis
- `BOT_TOKEN`: token do bot
- `TARGET_CHAT_ID`: destino padrão
- `PANEL_USER`: usuário do painel
- `PANEL_PASSWORD`: senha do painel
- `FLASK_SECRET`: chave aleatória

## Observação sobre o plano Free
O Web Service Free pode dormir após período sem tráfego. Como este projeto envia sob demanda pelo painel e não depende de polling contínuo, isso é menos problemático que um bot que precisa ficar monitorando mensagens o tempo todo.

## Segurança
Nunca publique o BOT_TOKEN no GitHub. Use apenas Environment Variables no Render.
