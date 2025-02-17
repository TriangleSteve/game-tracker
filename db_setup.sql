-- 1. Games Table
CREATE TABLE IF NOT EXISTS game (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

-- 2. Instances Table (Tracks user sessions for each game)
CREATE TABLE IF NOT EXISTS instance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL,
    username TEXT NOT NULL,
    hide_completed BOOLEAN DEFAULT 0,
    selected_categories TEXT DEFAULT '[]'
    FOREIGN KEY (game_id) REFERENCES game(id) ON DELETE CASCADE
);

-- 3. Checklist Table (Defines tasks per game)
CREATE TABLE IF NOT EXISTS checkbox (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    region TEXT,
    category TEXT,
    details TEXT,
    x INTEGER,
    y INTEGER,
    required BOOLEAN DEFAULT 0,
    FOREIGN KEY (game_id) REFERENCES game(id) ON DELETE CASCADE
);

-- 4. Checkbox Data Table (Tracks completion status)
CREATE TABLE IF NOT EXISTS checkbox_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    checkbox_id INTEGER NOT NULL,
    instance_id INTEGER NOT NULL,
    checked BOOLEAN DEFAULT 0,
    sort_order INTEGER;
    FOREIGN KEY (checkbox_id) REFERENCES checkbox(id) ON DELETE CASCADE,
    FOREIGN KEY (instance_id) REFERENCES instance(id) ON DELETE CASCADE
);
