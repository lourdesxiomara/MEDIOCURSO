# Sistema legado — descripción y muestra

`legado-almacen-muestra.csv` es una **muestra sintética** que reproduce la estructura del software actual
(`fecha, ingreso, salida, producto, nro_documento`) e incluye a propósito los defectos típicos de un
registro informal, para que la especificación de migración (`specs/06-migracion/`) los trate uno por uno.
Se reemplaza por la exportación real cuando esté disponible (duda D-06).

`id` es la clave interna del registro legado; se conserva para la trazabilidad.

## Defectos sembrados en la muestra
| Fila (id) | Defecto | Regla de migración |
|---|---|---|
| 3 | Fecha en formato `dd/mm/aaaa` | M-01 normalizar fecha |
| 4, 5 | Mismo producto con distinto texto / mayúsculas | M-03 normalizar y deduplicar producto |
| 5 | `nro_documento` sin serie (`88`) | M-04 documento no identificable |
| 6 | `nro_documento` vacío en un ingreso | M-04 |
| 7 | Serie mal escrita (`b1-89`) | M-04 reparación con revisión manual |
| 8 | Producto sujeto a ISC (cerveza) | M-06 marcar para catálogo 08 |
| 9 | Bolsas plásticas vendidas | M-06 marcar como sujeto a ICBPER |
| 10 | Cantidad negativa en `ingreso` y documento `AJUSTE` | M-02 / M-05 convertir en ajuste de inventario |
| 11 | Movimiento con ingreso y salida en 0 | M-02 descartar con registro en bitácora |
| 12 | Ingreso y salida en la misma fila | M-02 dividir en dos movimientos |
| 13 | Fecha vacía | M-01 cuarentena |
| 14 | Cantidad decimal en un producto por unidad | M-02 revisar unidad de medida |
| 15 | Documento `F001-125` repetido en otra fecha | M-04 posible duplicado |
