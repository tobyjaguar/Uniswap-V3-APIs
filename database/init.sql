-- Create the tokens table 
-- (if it has not already been created)
CREATE TABLE IF NOT EXISTS tokens (
    id SERIAL PRIMARY KEY,
    address VARCHAR(42) NOT NULL UNIQUE,
    symbol VARCHAR(10) NOT NULL UNIQUE,
    name VARCHAR(80) NOT NULL,
    decimals INTEGER NOT NULL,
    total_supply VARCHAR(80) NOT NULL,
    volume_usd VARCHAR(80) NOT NULL
);

-- Create the price_data table to store hourly price information
-- (if it has not already been created)
CREATE TABLE IF NOT EXISTS price_data (
    id SERIAL PRIMARY KEY,
    token_id INTEGER REFERENCES tokens(id),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    open NUMERIC(78, 18) NOT NULL,
    close NUMERIC(78, 18) NOT NULL,
    high NUMERIC(78, 18) NOT NULL,
    low NUMERIC(78, 18) NOT NULL,
    price_usd NUMERIC(78, 18) NOT NULL
);

-- Create an index on token_id and timestamp 
-- try to optimize the query performance
CREATE INDEX IF NOT EXISTS idx_price_data_token_timestamp ON price_data (token_id, timestamp);