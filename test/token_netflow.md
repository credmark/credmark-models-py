```sql
SELECT s.number    AS "s.number",
       s.timestamp AS "s.timestamp",
       s.number    AS "from_block",
       s.timestamp AS "from_timestamp",
       e.number    AS "to_block",
       e.timestamp AS "to_timestamp",
       Sum(CASE
             WHEN t.to_address = '0xa9d1e08c7793af67e9d92fe308d5697fb81d3e43'
           THEN
             t.value
             ELSE 0 :: INTEGER
           end)    AS "inflow",
       Sum(CASE
             WHEN t.from_address = '0xa9d1e08c7793af67e9d92fe308d5697fb81d3e43'
           THEN
             t.value
             ELSE 0 :: INTEGER
           end)    AS "outflow",
       Sum(CASE
             WHEN t.to_address = '0xa9d1e08c7793af67e9d92fe308d5697fb81d3e43'
           THEN
             t.value
             ELSE -t.value
           end)    AS "netflow"
FROM   raw_ethereum.public.blocks s
JOIN raw_ethereum.public.blocks e
ON e.number = ( ( s.number + 6516 ) - 1 )
LEFT OUTER JOIN raw_ethereum.public.transactions t
ON t.block_number BETWEEN s.number AND e.number
                       AND ( t.to_address =
                             '0xa9d1e08c7793af67e9d92fe308d5697fb81d3e43'
                              OR t.from_address =
                                 '0xa9d1e08c7793af67e9d92fe308d5697fb81d3e43' )
WHERE  s.number <= 14249443
       AND ( s.number > 14223379
             AND s.number <= 14249443 )
GROUP  BY s.number,
          s.timestamp,
          e.number,
          e.timestamp
HAVING s.number >= 14223379
       AND s.number < 14249443
       AND MOD(e.number - 14223379, 6516) = 0
ORDER  BY s.number ASC
LIMIT  5000
```

```sql
SELECT s.number    AS "s.number",
       s.timestamp AS "s.timestamp",
       s.number    AS "from_block",
       s.timestamp AS "from_timestamp",
       e.number    AS "to_block",
       e.timestamp AS "to_timestamp"
FROM   raw_ethereum.public.blocks s
JOIN raw_ethereum.public.blocks e
         ON e.number = ( ( s.number + 6516 ) - 1 )
WHERE  s.number <= 14249443
       AND ( s.number > 14223379
             AND s.number <= 14249443 )
GROUP  BY s.number,
          s.timestamp,
          e.number,
          e.timestamp
HAVING s.number >= 14223379
       AND s.number < 14249443
       AND MOD(e.number - 14223379, 6516) = 0
ORDER  BY s.number ASC
LIMIT  5000
```

```sql
SELECT Sum(CASE
             WHEN t.to_address = '0xa9d1e08c7793af67e9d92fe308d5697fb81d3e43'
           THEN
             t.value
             ELSE 0 :: INTEGER
           end)    AS "inflow",
       Sum(CASE
             WHEN t.from_address = '0xa9d1e08c7793af67e9d92fe308d5697fb81d3e43'
           THEN
             t.value
             ELSE 0 :: INTEGER
           end)    AS "outflow",
       Sum(CASE
             WHEN t.to_address = '0xa9d1e08c7793af67e9d92fe308d5697fb81d3e43'
           THEN
             t.value
             ELSE -t.value
           end)    AS "netflow"
FROM   raw_ethereum.public.transactions t
WHERE  t.block_number <= 14249443
       AND ( t.block_number > 14223379 AND t.block_number <= 14249443 )
```
