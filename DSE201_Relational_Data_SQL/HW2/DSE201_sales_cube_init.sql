-- Delete existing Tables
DROP TABLE IF EXISTS  "customers" CASCADE;
DROP TABLE IF EXISTS  "product_category" CASCADE;
DROP TABLE IF EXISTS  "products" CASCADE;
DROP TABLE IF EXISTS  "sales" CASCADE;
DROP TABLE IF EXISTS  "states" CASCADE;

-- Create tables for Sales Cube
CREATE TABLE states (
    id				SERIAL PRIMARY KEY,
    state_name      TEXT NOT NULL
);
CREATE TABLE customers (
    id          	SERIAL PRIMARY KEY,
    customer_name	TEXT NOT NULL,
    residence		INTEGER REFERENCES states (id)
);
CREATE TABLE product_category (
	id				SERIAL PRIMARY KEY,
	category		TEXT NOT NULL,
	description		TEXT
);
CREATE TABLE products (
    id          	SERIAL PRIMARY KEY,
    product_name	TEXT NOT NULL,
    list_price		NUMERIC,
    category_id		INTEGER REFERENCES product_category (id)
);
CREATE TABLE sales (
	id				SERIAL,
	quantity		INTEGER NOT NULL,
	sell_price		NUMERIC NOT NULL,
	customer_id		INTEGER REFERENCES customers (id) NOT NULL,
	product_id		INTEGER REFERENCES products (id) NOT NULL
);

-- Insert data into tables
INSERT INTO states (state_name) VALUES ('Arizona');
INSERT INTO states (state_name) VALUES ('California');
INSERT INTO states (state_name) VALUES ('Oregon');

INSERT INTO customers (customer_name, residence) VALUES ('Alice', 2);
INSERT INTO customers (customer_name, residence) VALUES ('Bob', 1);
INSERT INTO customers (customer_name, residence) VALUES ('Charlie', 2);
INSERT INTO customers (customer_name, residence) VALUES ('Denise', 3);

INSERT INTO product_category (category, description) VALUES ('Produce', 'Fruits and vegetables');
INSERT INTO product_category (category, description) VALUES ('Dairy', 'Stuff from cows');

INSERT INTO products (product_name, list_price, category_id) VALUES ('Apples', 0.99, 1);
INSERT INTO products (product_name, list_price, category_id) VALUES ('Bananas', 1.29, 1);
INSERT INTO products (product_name, list_price, category_id) VALUES ('Milk', 5.99, 2);
INSERT INTO products (product_name, list_price, category_id) VALUES ('Cheese', 1.99, 2);

INSERT INTO sales (quantity, sell_price, customer_id, product_id) VALUES (3, 0.99, 1, 1);
INSERT INTO sales (quantity, sell_price, customer_id, product_id) VALUES (2, 1.29, 2, 2);
INSERT INTO sales (quantity, sell_price, customer_id, product_id) VALUES (1, 5.99, 1, 3);