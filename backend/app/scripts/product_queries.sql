-- List products' usage count and quantity
-- user can filter by type(s)
SELECT
    product.name AS product_name,
    COUNT(op_input.*) AS usage_count,
    SUM(op_input.quantity) AS total_applied,
    quantity_unit
FROM "resource".product
    LEFT JOIN operation.op_input ON op_input.product_id = product.id
WHERE product.type IN ('Fertilizer')
GROUP BY product_id, product_name, op_input.quantity_unit
ORDER BY usage_count DESC, product_name;

-- List product usage instances
-- User can supply product name
SELECT 
    farm.name AS farm_name,
    field.name AS field_name,
    field_op.season,
    field_op.start AS application_timestamp,
    product.name AS product_name,
    op_input.area,
    op_input.area_unit,
    op_input.quantity,
    op_input.quantity_unit
FROM operation.op_input
    INNER JOIN "resource".product ON op_input.product_id = product.id
    AND product.name = 'Atrazine'
    LEFT JOIN operation.field_op ON op_input.op_id = field_op.id
    LEFT JOIN structure.field ON field_op.field_id = field.id
    LEFT JOIN structure.farm ON field.farm_id = farm.id
ORDER BY field_op.season;

-- Good Products to use: '28-0-0 UAN', 'Atrazine', 'Liberty Herbicide', 'harness extra', 'lumax', 'agrotain'
