# Docker Log to Telegram Forwarder
Questo script Python inoltra in tempo reale i log di un container Docker a una chat Telegram, con supporto per il filtraggio tramite espressioni regolari.

## 🧩 Funzionalità

- Connessione a Docker tramite socket locale (`/var/run/docker.sock`)
- Lettura continua dei log da un container specifico
- Filtraggio opzionale delle righe di log tramite regex (ad esempio: `ERROR|WARN`)
- Invio delle righe filtrate a un bot Telegram

## 🛠️ Requisiti

- Python 3.7 o superiore
- Accesso al socket Docker (`/var/run/docker.sock`)
- Bot Telegram (creato tramite BotFather)
- ID della chat o del gruppo dove inviare i log

### Dipendenze Python

Installa le dipendenze con:

```bash
pip install -r requirements.txt
```

## ⚙️ Configurazione

Definisci le seguenti variabili di ambiente:

| Variabile       | Descrizione                                      | Obbligatoria |
|-----------------|--------------------------------------------------|--------------|
| BOT_TOKEN       | Token del bot Telegram                           | ✅           |
| CHAT_ID         | ID della chat o gruppo di destinazione           | ✅           |
| CONTAINER_NAME  | Nome o ID del container da monitorare            | ✅           |
| LOG_NAME     | (Opzionale) nome del logger per log locali       | ❌           |
| LOG_REGEX       | (Opzionale) regex per filtrare i log             | ❌           |

## 🐳 Utilizzo con Docker

### Usando Docker Compose (consigliato)

1. Modifica il file `docker-compose.yml` con le tue variabili d'ambiente.
2. Avvia il container:

```bash
docker-compose up -d
```

## 🧪 Esempi di log inoltrati

Supponendo `CONTAINER_NAME=my_app` e log come:

```log
[INFO] Server started
[ERROR] Connection failed
```

Solo il secondo sarà inoltrato se `LOG_REGEX=ERROR`.

Su Telegram riceverai:

```
[my_app] [ERROR] Connection failed
```
