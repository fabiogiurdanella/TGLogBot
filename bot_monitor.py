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

async def telegram_worker(queue: asyncio.Queue):
    while True:
        text = await queue.get()
        try:
            await bot.send_message(chat_id=CHAT_ID, text=text)
        except TelegramError as exc:
            logging.error("Errore Telegram: %s", exc)
        await asyncio.sleep(0.5)  # Delay per evitare flood
        queue.task_done()

def main():
    container = dockercli.containers.get(CONTAINER_NAME)
    logging.info("In ascolto dei log di '%s'...", CONTAINER_NAME)
    log_stream = container.logs(stream=True, follow=True, tail=0)

    async def process_logs():
        queue = asyncio.Queue()
        worker = asyncio.create_task(telegram_worker(queue))
        try:
            for raw_line in log_stream:
                line = raw_line.decode("utf-8", errors="replace").rstrip()
                if LOGGER_NAME and LOGGER_NAME in line:
                    msg = line.split(LOGGER_NAME, 1)[-1].lstrip(" -:")
                    if msg:
                        if len(msg) > 4096:
                            msg = msg[-4096:]
                        await queue.put(f"[{CONTAINER_NAME}] {msg}")
        except KeyboardInterrupt:
            logging.info("Arresto richiesto dall'utente.")
        finally:
            await queue.join()
            worker.cancel()
            try:
                await worker
            except asyncio.CancelledError:
                pass

    asyncio.run(process_logs())

if __name__ == "__main__":
    main()