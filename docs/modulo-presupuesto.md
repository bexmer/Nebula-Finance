# Propuesta Estructurada para el Módulo de Presupuesto Completo

Esta propuesta resume y desarrolla el modelo funcional del módulo de presupuesto para Nebula Finance. Se organiza en cuatro pilares que abarcan todo el ciclo de planificación, ejecución, control y análisis financiero.

## Objetivos Generales

- Permitir la creación de presupuestos realistas que reflejen la naturaleza recurrente de los gastos e ingresos.
- Vincular las transacciones diarias con las partidas presupuestarias para medir la ejecución en tiempo real.
- Crear un "saldo presupuestado" que complemente la visión tradicional de cuentas bancarias.
- Proporcionar herramientas de cierre y análisis que faciliten el aprendizaje y la toma de decisiones para ciclos futuros.

## Pilar 1. Creación de un Presupuesto Flexible y Recurrente

### Validación
Un presupuesto estático de un solo mes es insuficiente. Las finanzas personales funcionan en ciclos, por lo que el módulo debe adaptarse a distintas frecuencias de ingresos y gastos.

### Requisitos Clave

1. **Frecuencia en las entradas de presupuesto**
   - Selector de frecuencia con opciones predefinidas: `Única vez`, `Mensual`, `Quincenal`, `Semanal`, `Anual` (valor por defecto: `Mensual`).
   - Campos de fecha que varían según la frecuencia:
     - `Única vez`: fecha específica del evento.
     - Recurrentes: fecha de inicio del ciclo.
2. **Control de recurrencia**
   - Casilla `Se repite siempre` (`is_recurring`) disponible para frecuencias recurrentes.
   - Al finalizar un período, si la casilla está activa, el sistema genera automáticamente la entrada para el siguiente ciclo (ej. duplicar Octubre → Noviembre).

### Implicaciones Técnicas

- Actualizar el modelo `BudgetEntry` con campos `frequency`, `start_date`, `end_date` y `is_recurring`.
- Ajustar formularios y validaciones de Frontend/Backend para soportar la captura de estos atributos.
- Planificar tareas de cron o jobs post-cierre que creen nuevas entradas cuando corresponda.

## Pilar 2. Vínculo Dinámico entre Presupuesto y Transacciones

### Validación
Sin la conexión entre lo planificado y lo ejecutado, el presupuesto es meramente aspiracional. La propuesta se centra en monitorear la ejecución en tiempo real.

### Requisitos Clave

1. **Asociar transacciones a partidas de presupuesto**
   - Campo opcional "Asociar a Presupuesto" en el formulario de transacciones.
   - El selector muestra únicamente las `BudgetEntry` activas del período en curso (según frecuencia y fechas definidas en el Pilar 1).
2. **Registro y acumulado del monto real**
   - Agregar un campo `actual_amount` en `BudgetEntry`.
   - Cada transacción asociada suma o resta (según sea gasto/ingreso) el valor al campo `actual_amount`.
3. **Visualización del progreso**
   - En la vista de presupuesto, mostrar para cada entrada: `Gastado / Presupuestado` junto con una barra de progreso.
   - Cambiar a un estado de alerta (color rojo, mensaje de sobre-ejecución) cuando `actual_amount > planned_amount`.

### Implicaciones Técnicas

- Extender el modelo de transacciones para almacenar el identificador de `BudgetEntry` asociado.
- Definir reglas de negocio para sincronizar `actual_amount` al crear/editar/eliminar transacciones.
- Actualizar componentes UI y endpoints de API para reflejar el progreso y las alertas.

## Pilar 3. Gestión de Saldos y "Cuenta de Presupuesto" Virtual

### Validación
La cuenta virtual separa el dinero disponible según el plan del dinero disponible en las cuentas bancarias, brindando una señal clara del margen de maniobra real.

### Requisitos Clave

1. **Creación automática de la cuenta virtual**
   - Cuenta "Saldo de Presupuesto" creada por defecto, no editable por el usuario.
   - Debe resaltarse visualmente (color, icono) para diferenciarla de cuentas reales.
2. **Cálculo del saldo presupuestado**
   - Saldo inicial = suma de montos presupuestados no ejecutados del período actual.
   - Cada transacción asociada a un presupuesto decrementa este saldo en el momento del registro.
3. **Sincronización con transacciones**
   - Al registrar un gasto, se afecta la cuenta real seleccionada y simultáneamente la cuenta virtual.
   - Para ingresos planificados, el saldo presupuestado aumenta cuando el ingreso real llega y se asocia al presupuesto.

### Implicaciones Técnicas

- Agregar lógica de backend que calcule dinámicamente el saldo de la cuenta virtual.
- Evitar que esta cuenta aparezca como editable en las pantallas de gestión de cuentas.
- Garantizar la consistencia del saldo cuando se modifican o eliminan transacciones asociadas a un presupuesto.

## Pilar 4. Cierre del Ciclo, Sobrantes y Análisis

### Validación
Un cierre ordenado permite aprender de los resultados, reasignar recursos y preparar el siguiente período con información confiable.

### Requisitos Clave

1. **Cierre de período**
   - Al vencer el período de una `BudgetEntry`, calcular automáticamente `Sobrante = planned_amount - actual_amount`.
   - Cambiar el estado de la entrada a "cerrada" y detener nuevas asociaciones de transacciones.
2. **Acciones sobre sobrantes y déficits**
   - Mostrar un resumen consolidado de sobrantes y déficits.
   - Opciones rápidas:
     - `Mover sobrante a ahorro`: generar una transacción de ingreso hacia una cuenta/objetivo de ahorro.
     - `Reiniciar próximo período`: archivar resultados y preparar el ciclo siguiente (creando nuevas entradas si la recurrencia sigue activa).
3. **Reporte de análisis**
   - Nuevo reporte "Análisis de Presupuesto" dentro del módulo de análisis.
   - Presentar tablas y gráficos comparando `Monto Presupuestado` vs `Monto Real` por categoría y por período.
   - Permitir filtros por rango de fechas, cuentas y etiquetas.

### Implicaciones Técnicas

- Implementar servicios o jobs que ejecuten el cierre al finalizar cada período.
- Diseñar componentes UI para el resumen de resultados y las acciones sugeridas.
- Integrar las nuevas métricas en la capa de analítica, preferiblemente reutilizando gráficos existentes.

## Próximos Pasos Recomendados

1. **Definición detallada del modelo de datos**
   - Diagramar las tablas afectadas (`BudgetEntry`, `Transaction`, `Account`) y definir migraciones.
2. **Diseño UX/UI**
   - Crear wireframes para las vistas de presupuesto, formularios y reportes.
3. **Plan de implementación iterativo**
   - Iteración 1: Campos de frecuencia y recurrencia (Pilar 1).
   - Iteración 2: Asociación con transacciones y visualizaciones básicas (Pilar 2).
   - Iteración 3: Cuenta virtual y sincronización de saldos (Pilar 3).
   - Iteración 4: Cierre, acciones y reportes (Pilar 4).
4. **Validación con usuarios**
   - Pilotar el módulo con un conjunto reducido de usuarios para ajustar reglas de negocio y UX.

Esta propuesta proporciona una hoja de ruta integral para construir un módulo de presupuesto robusto, flexible y centrado en la toma de decisiones basada en datos.
