-- SELECT field.name, ST_AsEWKT(geom)
-- FROM structure.field_boundary
-- JOIN structure.field ON field.id = field_id
-- WHERE field.name in ('MT-100', 'MT-200');

WITH params AS (
    SELECT
        2022 AS since_year,
        ARRAY['Seeding', 'Application'] AS operation_types,
        ARRAY['Herbicide'] AS product_types
), input_plots(plot_id, geom) AS (
    VALUES 
        (1, 'POINT(-88.2375 40.04880)'),
        (2, 'POINT(-88.2375 40.04890)'),
        (3, 'POINT(-88.2375 40.04900)'),
        (4, 'POINT(-88.2375 40.04910)'),
        (5, 'POINT(-88.2375 40.04920)'),
        (6, 'POINT(-88.2298 40.04855)')
), plot_fields AS (
    SELECT DISTINCT ON (p.plot_id) p.plot_id, ST_GeomFromText(p.geom, 4326) AS geom, fb.field_id
    FROM input_plots p
    JOIN structure.field_boundary fb ON ST_Covers(fb.geom, ST_GeomFromText(p.geom, 4326))
    ORDER BY p.plot_id, ST_Area(fb.geom)
)
SELECT 
    plot_id, ST_AsText(geom) AS geom,
    f.name AS field_name,
    op.type AS operation_type, op.season, op.start,
    product.name, product.brand, product.type AS product_type,
    inp.rate, inp.rate_unit
FROM plot_fields pf
JOIN structure.field f ON f.id = pf.field_id
JOIN operation.field_op op ON op.field_id = pf.field_id
LEFT JOIN operation.op_input inp ON inp.op_id = op.id
LEFT JOIN resource.product ON product.id = inp.product_id
CROSS JOIN params
WHERE op.season >= params.since_year
  AND op.type = ANY(params.operation_types)
--   AND (op.type != 'Application' OR product.type = ANY(params.product_types))
ORDER BY plot_id, season DESC, start DESC;
