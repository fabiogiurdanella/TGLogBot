# Docker Log to Telegram Forwarder

Questo script Python inoltra in tempo reale i log di un container Docker a una chat Telegram, con supporto per il filtraggio tramite espressioni regolari.

## 🧩 Funzionalità

- Connessione a Docker tramite socket locale (`/var/run/docker.sock`)
- Lettura continua dei log da un container specifico
- Filtraggio opzionale delle righe di log tramite regex (es. `ERROR|WARN`)
- Invio delle righe filtrate a un bot Telegram

## 🛠️ Requisiti

- Python 3.7+
- Accesso al socket Docker (`/var/run/docker.sock`)
- Bot Telegram (creato tramite BotFather)
- ID della chat o del gruppo dove inviare i log

### Dipendenze Python

Installabili con:

```bash
pip install -r requirements.txt
```

## ⚙️ Configurazione

Le seguenti variabili di ambiente devono essere definite:

| Variabile | Descrizione | Obbligatoria |
|-----------|-------------|--------------|
| BOT_TOKEN | Token del bot Telegram | ✅ |
| CHAT_ID | ID della chat o gruppo di destinazione | ✅ |
| CONTAINER_NAME | Nome o ID del container da monitorare | ✅ |
| LOG_REGEX | (Opzionale) Espressione regolare per filtrare | ❌ |

## 🐳 Utilizzo con Docker

### Usando Docker Compose (raccomandato)

1. Modifica il file `docker-compose.yml` con le tue variabili d'ambiente
2. Avvia il container:

```bash
docker-compose up -d
```

### Esecuzione locale

1. Assicurati che il container Docker da monitorare sia in esecuzione
2. Avvia lo script:

```bash
python bot_monitor.py
```

I log corrispondenti (o tutti, se `LOG_REGEX` è omesso) saranno inoltrati al bot Telegram nella chat specificata.

## 🧪 Esempi di log inoltrati

Con `CONTAINER_NAME=my_app` e log che includono:

```log
[INFO] Server started
[ERROR] Connection failed
```

Solo il secondo sarà inoltrato se `LOG_REGEX=ERROR`.

Telegram riceverà:

```
[my_app] [ERROR] Connection failed
```

## ❗ Avvertenze

- Lo script è pensato per essere eseguito all'interno di un ambiente che abbia accesso al socket Docker
- In caso di errore nel bot Telegram (token errato, chat non autorizzata, ecc.), i messaggi verranno loggati localmente