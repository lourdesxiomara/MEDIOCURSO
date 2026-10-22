# Legacy system — description and sample

`legado-almacen-muestra.csv` is a **synthetic sample** that reproduces the structure of the current software
(`fecha, ingreso, salida, producto, nro_documento`) and deliberately includes the typical defects of an
informal record, so that the migration spec (`specs/06-migracion/`) handles them one by one.
It is replaced by the real export when available (question D-06). Data values stay in Spanish, as in the source system.

`id` is the internal key of the legacy row; it is kept for traceability.

## Defects seeded in the sample
| Row (id) | Defect | Migration rule |
|---|---|---|
| 3 | Date in `dd/mm/yyyy` format | M-01 normalize date |
| 4, 5 | Same product with different text / case | M-03 normalize and deduplicate product |
| 5 | `nro_documento` without series (`88`) | M-04 unidentifiable document |
| 6 | Empty `nro_documento` on an input | M-04 |
| 7 | Mistyped series (`b1-89`) | M-04 repair with manual review |
| 8 | Product subject to ISC (beer) | M-06 flag for catalog 08 |
| 9 | Plastic bags sold | M-06 flag as subject to ICBPER |
| 10 | Negative `ingreso` and document `AJUSTE` | M-02 / M-05 convert into an inventory adjustment |
| 11 | Movement with input and output both 0 | M-02 discard and log |
| 12 | Input and output on the same row | M-02 split into two movements |
| 13 | Empty date | M-01 quarantine |
| 14 | Decimal quantity on a per-unit product | M-02 review unit of measure |
| 15 | Document `F001-125` repeated on another date | M-04 possible duplicate |
