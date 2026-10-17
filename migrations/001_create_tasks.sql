CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    completed BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT task_title_not_empty
        CHECK (length(trim(title)) > 0)
);