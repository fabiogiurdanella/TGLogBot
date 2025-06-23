#!/usr/bin/env python3
import asyncio
import logging
import os
import time
from typing import Optional

from docker import from_env
from telegram.error import TelegramError
from telegram.ext import Application, AIORateLimiter


# ------------------------------------------------------------------#
# Variabili d'ambiente obbligatorie                                 #
# ------------------------------------------------------------------#
BOT_TOKEN      = os.getenv("BOT_TOKEN")       # token BotFather
CHAT_ID        = os.getenv("CHAT_ID")         # chat o gruppo di destinazione
CONTAINER_NAME = os.getenv("CONTAINER_NAME")  # nome o ID del container
LOGGER_NAME    = os.getenv("LOGGER_NAME")     # (opzionale) tag logger da filtrare

if not all([BOT_TOKEN, CHAT_ID, CONTAINER_NAME]):
    raise RuntimeError("BOT_TOKEN, CHAT_ID e CONTAINER_NAME sono obbligatori")

# ------------------------------------------------------------------#
# Logging locale                                                    #
# ------------------------------------------------------------------#
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")


# ------------------------------------------------------------------#
# Producer: legge i log e mette ogni riga nella coda                #
# ------------------------------------------------------------------#
async def stream_logs(queue: asyncio.Queue, *, tag: Optional[str]) -> None:
    docker = from_env()
    container = docker.containers.get(CONTAINER_NAME)
    logging.info("In ascolto dei log di '%s' …", CONTAINER_NAME)

    # since=… evita di reinviare log storici dopo un riavvio
    log_stream = container.logs(stream=True,
                                follow=True,
                                tail=0,
                                since=int(time.time()))

    for raw in log_stream:
        line = raw.decode("utf-8", "replace").rstrip()

        # Facoltativo: filtra solo le righe che contengono il tag del logger
        if tag and tag not in line:
            continue

        # Rimuove il tag dal testo (se presente)
        if tag:
            line = line.split(tag, 1)[-1].lstrip(" -:")

        # Telegram consente max 4096 caratteri per messaggio
        await queue.put(line[-4096:])


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

    producer = asyncio.create_task(stream_logs(queue, tag=LOGGER_NAME))
    sender   = asyncio.create_task(telegram_sender(bot, queue))

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
