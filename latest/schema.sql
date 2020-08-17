DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS transactions;

CREATE TABLE users
(
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    name     VARCHAR(255),
    coins    JSON,
    joinTime TIMESTAMP                                  DEFAULT CURRENT_TIMESTAMP,
    isValid  BOOLEAN NOT NULL CHECK (isValid IN (0, 1)) DEFAULT 1,
    isAdmin  BOOLEAN NOT NULL CHECK (isValid IN (0, 1)) DEFAULT 0,
    token    VARCHAR(255)                               DEFAULT 'BLANK'
);

CREATE TABLE transactions
(
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    fromUser     VARCHAR(255),
    toUser       VARCHAR(255),
    coins        JSON,
    notes        VARCHAR(255),
    transferTime TIMESTAMP                                     DEFAULT CURRENT_TIMESTAMP,
    isVisible    BOOLEAN NOT NULL CHECK (isVisible IN (0, 1))  DEFAULT 1,
    readByUser   BOOLEAN NOT NULL CHECK (readByUser IN (0, 1)) DEFAULT 0
);


CREATE TABLE forums
(
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        VARCHAR(255),
    admins      JSON,
    owners      JSON,
    lastBalance INTEGER NOT NULL CHECK (lastBalance > -1) DEFAULT 0,
    joinTime    TIMESTAMP                                 DEFAULT CURRENT_TIMESTAMP
);
