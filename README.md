# Expense Tracker AI

Asistente conversacional de registro de gastos personales impulsado por LLM. Le hablás en lenguaje natural y él detecta, extrae y guarda el gasto en una base de datos — sin formularios ni categorías manuales.

## Cómo funciona

```
Tu mensaje → Extractor (GPT-4o-mini) → ¿es un gasto?
                                              ↓ sí
                                         Postgres (gastos)
                                              ↓
                               LLM confirma con datos estructurados
                                              ↓
                          Redis guarda el historial de la sesión
                                              ↓
                    Al cerrar: Postgres + ChromaDB guardan el resumen
                    Al abrir:  ChromaDB recupera contexto relevante
```

**Stack:**
- **LangChain + GPT-4o-mini** — extracción y conversación
- **PostgreSQL** — gastos y resúmenes de sesión persistentes
- **Redis** — memoria de conversación en sesión activa (con compresión automática)
- **ChromaDB** — búsqueda semántica de historial entre sesiones
- **Docker Compose** — levanta Postgres y Redis con un comando

## Requisitos previos

- Python 3.11+
- Docker Desktop (para Postgres y Redis)
- Una API key de OpenAI

## Instalación

**1. Clonar el repositorio**

```bash
git clone <url-del-repo>
cd expense-tracker-ai
```

**2. Crear y activar el entorno virtual**

```bash
py -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux
```

**3. Instalar dependencias**

```bash
pip install -r requirements.txt
```

**4. Configurar variables de entorno**

Crear un archivo `.env` en la raíz del proyecto con el siguiente contenido:

```env
# OpenAI
OPENAI_API_KEY=sk-...

# LangSmith (opcional — para trazabilidad)
LANGCHAIN_TRACING_V2=false
LANGCHAIN_API_KEY=
LANGCHAIN_PROJECT=gastos-ai

# Postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=expense_user
POSTGRES_PASSWORD=expense_pass
POSTGRES_DB=expense_db

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
```

**5. Levantar la infraestructura**

```bash
docker compose up -d
```

Esto inicia Postgres (con el schema creado automáticamente desde `db/schema.sql`) y Redis.

**6. Verificar que todo esté corriendo**

```bash
docker compose ps
```

Ambos servicios deben aparecer como `healthy`.

## Ejecutar

```bash
python -c "
from app.main import chat
print(chat('Gasté 45 soles en almuerzo hoy'))
print(chat('¿Cuánto gasté esta semana?'))
"
```

O integrarlo en cualquier interfaz (CLI, API, etc.) importando `chat()` desde `app.main`.

## Ejemplo de uso

```
Usuario: gasté 120 soles en nafta ayer
Bot:     Registrado: S/ 120.00 en transport. ¿Necesitás agregar algo más?

Usuario: y 35 en café esta mañana
Bot:     Registrado: S/ 35.00 en food.

Usuario: ¿cuánto gasté en total?
Bot:     Hasta ahora llevas S/ 155.00 registrados.
```

## Estructura del proyecto

```
expense-tracker-ai/
├── app/
│   ├── main.py          # punto de entrada — función chat()
│   ├── extractor.py     # extrae datos del gasto con structured output
│   ├── storage.py       # lectura/escritura en Postgres
│   ├── memory.py        # historial Redis con compresión y flush a Postgres
│   └── vector_store.py  # embeddings y búsqueda semántica con ChromaDB
├── db/
│   └── schema.sql       # tablas expenses y session_summaries
├── data/
│   └── chroma/          # índice vectorial local (generado automáticamente)
├── docker-compose.yml
├── requirements.txt
└── .env                 # no commitear — contiene keys privadas
```

## Comandos útiles

```bash
# Ver tablas en Postgres
docker compose exec postgres psql -U expense_user -d expense_db -c "\dt"

# Ver gastos registrados
docker compose exec postgres psql -U expense_user -d expense_db -c "SELECT * FROM expenses;"

# Detener la infraestructura
docker compose down

# Detener y borrar datos (reset completo)
docker compose down -v
```
