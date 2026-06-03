-- tabla de gastos
CREATE TABLE IF NOT EXISTS expenses (
    id          SERIAL PRIMARY KEY,
    amount      NUMERIC(10, 2)  NOT NULL CHECK (amount > 0),
    category    VARCHAR(50)     NOT NULL,
    description TEXT            NOT NULL,
    expense_date DATE           NOT NULL,
    created_at  TIMESTAMP       DEFAULT NOW()
);

-- índices para queries frecuentes
CREATE INDEX IF NOT EXISTS idx_expenses_date
    ON expenses (expense_date);

CREATE INDEX IF NOT EXISTS idx_expenses_category
    ON expenses (category);

CREATE TABLE IF NOT EXISTS session_summaries (
    id           SERIAL PRIMARY KEY,
    session_id   TEXT          NOT NULL,
    summary      TEXT          NOT NULL,
    created_at   TIMESTAMP     DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_summaries_session
    ON session_summaries (session_id);

CREATE INDEX IF NOT EXISTS idx_summaries_created
    ON session_summaries (created_at);