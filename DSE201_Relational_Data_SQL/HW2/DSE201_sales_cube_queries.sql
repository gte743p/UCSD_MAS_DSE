-- Show the total sales (quantity sold and dollar value) for each customer
SELECT customer_id, quantity, sum(sell_price)
FROM sales
GROUP BY quantity, customer_id

-- updated #1
SELECT customer_id, sum(quantity) as total_items, sum(quantity * price) as total_sales
FROM sale
GROUP BY customer_id
ORDER BY customer_id

-- Show the total sales for each state
SELECT state_name, sum(sell_price)
FROM sales, states, customers
WHERE sales.customer_id = customers.id AND states.id = customers.residence
GROUP BY state_name

-- updated #2
SELECT state_name, sum(quantity*price) as total_sales
FROM sales.sale, sales.state, sales.customer
WHERE sale.customer_id = customer.customer_id AND state.state_id = customer.state_id
GROUP BY state_name

-- Show the total sales for each product, for a given customer.
-- Only products that were actually bought by the given customer are listed.
-- Order by dollar value.
SELECT c.customer_name, p.product_name, SUM(s.sell_price)
FROM sales s, customers c, products p
WHERE s.customer_id = c.id AND s.product_id = p.id
GROUP BY c.customer_name, p.product_name
ORDER BY SUM(s.sell_price) DESC

-- updated #3 for customer_name = 'Christine'
SELECT c.customer_id, c.customer_name, p.product_name, SUM(s.quantity*s.price) as total_sales
FROM sales.sale s, sales.customer c, sales.product p
WHERE c.customer_name = 'Christine' AND s.customer_id = c.customer_id AND s.product_id = p.product_id
GROUP BY c.customer_id, c.customer_name, p.product_name
ORDER BY total_sales DESC

-- Show the total sales for each product and customer. Order by dollar value.
WITH all_p_c AS
(SELECT pAll.product_name, cAll.customer_name
FROM products pAll, customers cAll),
total_sales AS
(SELECT c.customer_name, p.product_name, SUM(s.sell_price) AS sales_total
FROM sales s, customers c, products p
WHERE s.customer_id = c.id AND s.product_id = p.id
GROUP BY c.customer_name, p.product_name
ORDER BY sales_total DESC)
SELECT all_p_c.product_name, all_p_c.customer_name, total_sales.sales_total
FROM all_p_c LEFT OUTER JOIN total_sales ON 
	all_p_c.product_name = total_sales.product_name AND
    all_p_c.customer_name = total_sales.customer_name
ORDER BY sales_total DESC NULLS LAST

-- updated #4
WITH all_p_c AS
(SELECT pAll.product_name, cAll.customer_name
FROM sales.product pAll, sales.customer cAll),
total_sales AS
(SELECT c.customer_name, p.product_name, SUM(s.quantity*s.price) AS sales_total
FROM sales.sale s, sales.customer c, sales.product p
WHERE s.customer_id = c.customer_id AND s.product_id = p.product_id
GROUP BY c.customer_name, p.product_name
ORDER BY sales_total DESC)
SELECT all_p_c.product_name, all_p_c.customer_name, coalesce(total_sales.sales_total,0)
FROM all_p_c LEFT OUTER JOIN total_sales ON 
	all_p_c.product_name = total_sales.product_name AND
    all_p_c.customer_name = total_sales.customer_name
ORDER BY sales_total DESC NULLS LAST

-- Show the total sales for each product category and state.
WITH all_comb AS
(SELECT pcAll.category, stAll.state_name
FROM product_category pcAll, states stAll),
total_sales AS
(SELECT st.state_name, pc.category, SUM(s.sell_price) AS sales_total
FROM sales s, customers c, states st, products p, product_category pc
WHERE s.customer_id = c.id AND s.product_id = p.id AND
	st.id = c.residence AND p.category_id = pc.id
GROUP BY st.state_name, pc.category)
SELECT all_comb.state_name, all_comb.category, total_sales.sales_total
FROM all_comb LEFT OUTER JOIN total_sales ON 
	all_comb.state_name = total_sales.state_name AND
    all_comb.category = total_sales.category
ORDER BY sales_total DESC NULLS LAST

-- updated #5
WITH all_comb AS
(SELECT pcAll.category_id, pcAll.category_name, stAll.state_id, stAll.state_name
FROM sales.category pcAll, sales.state stAll),
total_sales AS
(SELECT st.state_name, pc.category_id, SUM(s.quantity*s.price) AS sales_total
FROM sales.sale s, sales.customer c, sales.state st, sales.product p, sales.category pc
WHERE s.customer_id = c.customer_id AND s.product_id = p.product_id AND
	st.state_id = c.state_id AND p.category_id = pc.category_id
GROUP BY st.state_name, pc.category_id)
SELECT all_comb.state_id, all_comb.state_name, all_comb.category_id, all_comb.category_name, COALESCE(total_sales.sales_total,0) as total_sales
FROM all_comb LEFT OUTER JOIN total_sales ON 
	all_comb.state_name = total_sales.state_name AND
    all_comb.category_id = total_sales.category_id
ORDER BY sales_total DESC NULLS LAST

-- For each one of the top 20 product categories and top 20 customers, 
-- return a tuple (top product, top customer, quantity sold, dollar value)

-- 400 rows

-- top 20 product categories
SELECT pc.category, SUM(s.quantity) AS qty, SUM(s.sell_price) AS sales
FROM sales s, products p, product_category pc
WHERE s.product_id = p.id AND p.category_id = pc.id
GROUP BY pc.category
ORDER BY sales DESC
LIMIT 20

-- top 20 customers
SELECT c.customer_name, SUM(s.quantity) AS qty, SUM(s.sell_price) AS sales
FROM sales s, customers c
WHERE s.customer_id = c.id
GROUP BY c.customer_name
ORDER BY sales DESC
LIMIT 20

-- top 20 states
SELECT st.state_name, SUM(s.quantity) AS qty, SUM(s.sell_price) AS sales
FROM sales s, customers c, states st
WHERE s.customer_id = c.id AND c.residence = st.id
GROUP BY st.state_name
ORDER BY sales DESC
LIMIT 20

-- join product names, product categories, customer name, customer state to sales table
SELECT pc.category, st.state_name, c.customer_name, p.product_name, s.quantity, s.sell_price
FROM sales s, products p, product_category pc, customers c, states st
WHERE s.customer_id = c.id AND s.product_id = p.id AND p.category_id = pc.id AND
	c.residence = st.id

-- group joined table by product category, state, customer name, product name and 
-- sum sales and qty info, then take max
WITH s AS
(SELECT pc.category, st.state_name, c.customer_name, p.product_name, s.quantity, s.sell_price
FROM sales s, products p, product_category pc, customers c, states st
WHERE s.customer_id = c.id AND s.product_id = p.id AND p.category_id = pc.id AND
	c.residence = st.id)
SELECT s.category, s.state_name, s.customer_name, s.product_name, MAX(SUM(s.quantity)), 
	MAX(SUM(s.sell_price))
FROM s

-- left outer join resultant table to cross product table of product_category and state

-- full query
WITH s AS
(SELECT pc.category, st.state_name, c.customer_name, p.product_name, s.quantity, s.sell_price
FROM sales s, products p, product_category pc, customers c, states st
WHERE s.customer_id = c.id AND s.product_id = p.id AND p.category_id = pc.id AND
	c.residence = st.id),
s1 AS 
(SELECT s.category, s.state_name, s.customer_name, s.product_name, SUM(s.quantity) AS quantity, SUM(s.sell_price) AS sales
FROM s
GROUP BY s.category, s.state_name, s.customer_name, s.product_name),
max_s AS
(SELECT s1.category, s1.state_name, MAX(s1.quantity) AS max_qty, MAX(s1.sales) AS max_sales
FROM s1
GROUP BY s1.category, s1.state_name),
max_s1 AS
(SELECT s1.category AS product_category, s1.state_name AS state, s1.customer_name AS customer, s1.product_name AS product, max_s.max_qty AS quantity, max_s.max_sales AS sales
FROM s1, max_s
WHERE s1.category = max_s.category AND s1.state_name = max_s.state_name AND s1.quantity = max_s.max_qty AND
	s1.sales = max_s.max_sales),
all_groups AS
(SELECT pc1.category, st1.state_name
FROM product_category pc1, states st1)
SELECT all_groups.category, max_s1.state, max_s1.customer, max_s1.product, max_s1.quantity, max_s1.sales
FROM all_groups LEFT OUTER JOIN max_s1 ON max_s1.product_category = all_groups.category AND
	max_s1.state = all_groups.state_name