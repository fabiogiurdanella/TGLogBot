#!/usr/bin/env python3
import asyncio
import logging
import os
import time
import re

from docker import from_env
from telegram.error import TelegramError
from telegram.ext import Application, AIORateLimiter


# ------------------------------------------------------------------#
# Variabili d'ambiente obbligatorie                                 #
# ------------------------------------------------------------------#
BOT_TOKEN      = os.getenv("BOT_TOKEN")
CHAT_ID        = os.getenv("CHAT_ID")
CONTAINER_NAME = os.getenv("CONTAINER_NAME")
LOG_NAME    = os.getenv("LOG_NAME", None)
LOG_REGEX   = os.getenv("LOG_REGEX", None)

if not all([BOT_TOKEN, CHAT_ID, CONTAINER_NAME]):
    raise RuntimeError("BOT_TOKEN, CHAT_ID, CONTAINER_NAME sono obbligatori")

# ------------------------------------------------------------------#
# Logging locale                                                    #
# ------------------------------------------------------------------#
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")


# ------------------------------------------------------------------#
# Producer: legge i log e mette ogni riga nella coda                #
# ------------------------------------------------------------------#
async def stream_logs(queue: asyncio.Queue) -> None:
    docker = from_env()
    container = docker.containers.get(CONTAINER_NAME)

    logging.info("Inizio a leggere i log del container %s", CONTAINER_NAME)
    
    loop = asyncio.get_running_loop()
    
    def reader():
        for raw in container.logs(stream=True, follow=True, since=int(time.time() - 60)):
            line = raw.decode(errors="replace").rstrip()
            if LOG_NAME and LOG_NAME not in line:
                continue
            if LOG_REGEX and not re.search(LOG_REGEX, line):
                continue
            # Si consegna il messaggio alla coda, nel thread principale
            asyncio.run_coroutine_threadsafe(queue.put(line[:4096]), loop)

    # Thread per leggere i log del container
    await asyncio.to_thread(reader)


# ------------------------------------------------------------------#
# Consumer: estrae dalla coda e invia su Telegram                   #
# ------------------------------------------------------------------#
async def telegram_sender(bot, queue: asyncio.Queue) -> None:
    while True:
        text = await queue.get()
        try:
            await bot.send_message(chat_id=CHAT_ID, text=text)
        except TelegramError as exc:
            # Qualsiasi errore (inclusi i rarissimi non-429) viene soltanto loggato
            logging.error("Errore Telegram: %s", exc)
        finally:
            queue.task_done()


# ------------------------------------------------------------------#
# Main                                                              #
# ------------------------------------------------------------------#
async def main() -> None:
    # Costruiamo l’application con il rate-limiter abilitato
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .rate_limiter(AIORateLimiter())     # usa i bucket di default
        .build()
    )
    await application.initialize()          # apre la sessione HTTP
    bot = application.bot                   # lo riutilizzeremo sotto

    # Coda: ogni elemento è un singolo messaggio di log
    queue = asyncio.Queue(maxsize=1000)     # back-pressure minimo

    producer = asyncio.create_task(stream_logs(queue=queue))
    sender   = asyncio.create_task(telegram_sender(bot=bot, queue=queue))

    try:
        await asyncio.gather(producer, sender)
    finally:
        # Terminazione pulita
        await queue.join()
        producer.cancel()
        sender.cancel()
        await application.shutdown()
        logging.info("Terminato.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Interrotto dall’utente.")