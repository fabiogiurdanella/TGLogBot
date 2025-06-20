import os
import re
import logging
from docker import from_env
from telegram import Bot
import asyncio
from telegram.error import TelegramError

# --- Config da variabili d'ambiente ------------------------------
BOT_TOKEN       = os.getenv("BOT_TOKEN")        # token BotFather
CHAT_ID         = os.getenv("CHAT_ID")          # chat / gruppo di destinazione
CONTAINER_NAME  = os.getenv("CONTAINER_NAME")   # nome o ID del container
LOGGER_NAME     = os.getenv("LOGGER_NAME")           # nome del logger Python
# -----------------------------------------------------------------

if not all([BOT_TOKEN, CHAT_ID, CONTAINER_NAME]):
    raise RuntimeError("BOT_TOKEN, CHAT_ID e CONTAINER_NAME sono obbligatori.")

bot       = Bot(BOT_TOKEN)
dockercli = from_env()          # usa /var/run/docker.sock montato nel container

# Logging locale (non mandiamo tutto su Telegram se non serve)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

def send_telegram_message(text: str) -> None:
    """Invia `text` alla chat Telegram specificata."""
    try:
        asyncio.run(bot.send_message(chat_id=CHAT_ID, text=text))
    except TelegramError as exc:
        logging.error("Errore Telegram: %s", exc)


def main() -> None:
    container = dockercli.containers.get(CONTAINER_NAME)
    logging.info("In ascolto dei log di '%s'...", CONTAINER_NAME)

    # stream=True restituisce un generatore che blocca finché arrivano log
    log_stream = container.logs(stream=True, follow=True, tail=0)

    for raw_line in log_stream:
        line = raw_line.decode("utf-8", errors="replace").rstrip()

        # Invia solo se LOGGER_NAME è presente nella riga
        if LOGGER_NAME and LOGGER_NAME in line:
            # Estrai la sottostringa dopo la prima occorrenza di LOGGER_NAME
            msg = line.split(LOGGER_NAME, 1)[-1].lstrip(" -:")
            # Controlla che la stringa non sia vuota e non superi 4096 caratteri
            if msg:
                if len(msg) > 4096:
                    msg = msg[-4096:]
                send_telegram_message(f"[{CONTAINER_NAME}] {msg}")
                # Timeout per evitare flood
                asyncio.run(asyncio.sleep(0.5))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Arresto richiesto dall'utente.")