# 🤖 peliculas_series_novelas_daya BOT

Bot de Telegram que busca y publica automáticamente contenido de novelas, series y películas completas.

## Configuración

### Variables de entorno requeridas (en Replit Secrets):
- `TELEGRAM_BOT_TOKEN` — Token de @BotFather
- `TELEGRAM_CHANNEL_ID` — ID o @username del canal

### Variables opcionales:
- `MONETIZATION_DOMAIN` — Tu dominio de monetización (ej: `midominio.com`)
- `PUBLISH_INTERVAL_HOURS` — Cada cuántas horas publicar (default: `4`)
- `ITEMS_PER_RUN` — Cuántos posts por ciclo (default: `3`)
- `DELAY_BETWEEN_POSTS` — Segundos entre posts (default: `60`)

## Cómo ejecutar

```bash
cd bot
python main.py
```

## Estructura

- `main.py` — Punto de entrada
- `scheduler.py` — Programador de ciclos automáticos
- `searcher.py` — Busca contenido en YouTube y OK.ru
- `publisher.py` — Construye y envía mensajes a Telegram
- `hashtags.py` — Genera hashtags automáticos

## Agregar dominio de monetización

En Replit Secrets, agrega:
- Key: `MONETIZATION_DOMAIN`
- Value: `tudominio.com`

Los enlaces se convertirán en: `https://tudominio.com/?redirect=<url_original>`
