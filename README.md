# Opos Asturias Bot

Bot en Python que revisa fuentes de empleo público en Asturias y envía avisos por Telegram. Está pensado para ejecutarse diariamente con GitHub Actions, guardando estado en el propio repositorio.

## Requisitos

- Python 3.12
- Dependencias: `requests`, `beautifulsoup4`, `PyYAML`, `python-dateutil`

## Configuración de Telegram

1. Crea un bot con **@BotFather** y obtén el `BOT_TOKEN`.
2. Obtén tu `CHAT_ID`:
   - Envía un mensaje a tu bot.
   - Visita: `https://api.telegram.org/bot<tu_token>/getUpdates`
   - Busca el campo `chat.id`.
3. Configura los secretos en GitHub:
   - `BOT_TOKEN`
   - `CHAT_ID`
   - `REPO_PUSH_TOKEN` (opcional, pero recomendado si el `GITHUB_TOKEN` no puede hacer `git push`)

### Permisos del workflow

Si ves errores `403` al hacer `git push` desde Actions, revisa:

- **Settings → Actions → General → Workflow permissions**: debe estar en **Read and write**.
- Si tienes protección de rama en `main`, permite que GitHub Actions pueda hacer push o crea una excepción para el bot.
- Alternativamente, crea un **Personal Access Token (classic)** con scope `repo` y guárdalo como `REPO_PUSH_TOKEN` para que el workflow empuje con ese token.

## Configuración de fuentes

Edita `data/sources.yaml` para añadir o ajustar fuentes. Cada fuente puede definir:

- `id`: identificador único.
- `name`: nombre visible.
- `type`: `sta`, `principado` o `age`.
- `url`: URL a consultar.
- `include_keywords`: lista de palabras clave (si está vacía se usan los defaults globales).
- `exclude_keywords`: lista de palabras excluidas (si está vacía se usan los defaults globales).
- `match_any`: si `true`, no aplica filtros y avisa de todo.

### Limitaciones conocidas

- El filtrado por keywords solo revisa título, fechas y organismo (no URLs) para evitar falsos positivos por rutas internas.
- El buscador de AGE (`age`) puede requerir filtros adicionales o parámetros. Si la web cambia y no devuelve resultados con la página base, el bot registrará un aviso en logs y seguirá con el resto de fuentes.
- En sedes tipo STA se recorren enlaces de empleo/tablon detectados y hasta 3 páginas de paginación para evitar abusar.

## Ejecución local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m src.main
```

Si no defines `BOT_TOKEN` y `CHAT_ID`, el script funcionará en modo **dry-run** y solo mostrará logs.

## GitHub Actions

El workflow `daily.yml` ejecuta el bot diariamente a las **06:30 UTC** y hace commit de `data/state.json` si cambia.

## Estructura del proyecto

- `src/main.py`: orquestación y filtros.
- `src/sources/`: adaptadores por fuente.
- `data/sources.yaml`: configuración de fuentes y keywords.
- `data/state.json`: estado de ítems vistos.
