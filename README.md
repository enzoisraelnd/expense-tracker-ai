-- crear entorno
py -m venv venv

-- iniciar entorno
venv\Scripts\activate

-- purga intalacion de requirements
pip cache purge

-- instalacion de requirements
pip install -r requirements.txt

-- iniciando recursos
docker compose up -d

-- verificando tabla
docker compose exec postgres psql -U expense_user -d expense_db -c "\dt"