# AI Decision Log — TicketLite Cloud

Este documento registra las decisiones técnicas tomadas durante el desarrollo con asistencia de herramientas de IA (Claude, de Anthropic, usado como asistente de diseño de arquitectura y pair-programming conversacional). Cada entrada documenta el problema abordado, qué se le pidió a la IA, qué propuso, y qué validación o corrección humana se aplicó antes de llevarlo a producción.

---

## 1. Arquitectura de notificaciones asíncronas (SQS + Lambda + SNS/SES)

**Problema abordado:** Notificar a los usuarios cuando cambia el estado de un ticket, sin acoplar ese envío a la request HTTP del usuario (que no debería esperar a que un email salga para recibir su respuesta).

**Prompt / Herramienta utilizada:** Se consultó a Claude sobre qué servicios de AWS permitían resolver un flujo de notificaciones desacoplado y gestionado, partiendo de una aplicación Django ya existente.

**Código / Arquitectura generada:** Se propuso un flujo con un `signal` de Django sobre el modelo `HistorialEstado` que publica un mensaje en una cola Amazon SQS; la cola dispara una función AWS Lambda, que a su vez publica el aviso en Amazon SNS (más tarde también SES) para el envío del email.

**Validación y Corrección Humana:** Cada pieza se probó manualmente en la consola de AWS antes de integrarla (mensajes de prueba en SQS, verificación de logs en CloudWatch, confirmación de la suscripción SNS) en vez de asumir que el código generado funcionaría en el primer intento. Además, la primera versión del signal no contemplaba qué pasaba si AWS no respondía; se identificó que un fallo de red podía impedir la creación del ticket completo, y se corrigió agregando manejo de errores (`try/except`) para que la notificación sea best-effort y nunca bloquee la operación principal del usuario.

---

## 2. Elección del mecanismo de IA para sugerir prioridad

**Problema abordado:** Incorporar un componente de inteligencia artificial que sugiera automáticamente la prioridad de un ticket nuevo, evaluando si debía resolverse dentro de la misma infraestructura de AWS (vía Bedrock, invocado desde la Lambda) o como una llamada directa desde Django.

**Prompt / Herramienta utilizada:** Se le pidió a Claude comparar ambos enfoques en términos de complejidad de integración, dado que la app ya tenía el flujo síncrono de creación de tickets resuelto.

**Código / Arquitectura generada:** Se sugirió resolverlo con una llamada síncrona a la API de Gemini directamente desde `TicketCreateView`, en lugar de coordinar una respuesta asíncrona entre Django y una Lambda invocando Bedrock.

**Validación y Corrección Humana:** Se evaluó el trade-off explícitamente: usar un proveedor distinto al resto de la infraestructura (AWS) simplifica la integración a costa de no mantener todo bajo el mismo proveedor cloud. Se documentó esa justificación como decisión consciente, tal como exige la libertad tecnológica de la cátedra, en lugar de adoptar la sugerencia sin cuestionarla.

---

## 3. Corrección de un modelo de IA deprecado en producción

**Problema abordado:** Al probar la funcionalidad de prioridad automática, la aplicación falló con un error 404 indicando que el modelo `gemini-2.0-flash` ya no estaba disponible.

**Prompt / Herramienta utilizada:** Se compartió el traceback completo del error con Claude para diagnosticarlo.

**Código / Arquitectura generada:** Se identificó que el modelo había sido retirado y que, además, la librería utilizada (`google-generativeai`) estaba deprecada en favor del paquete nuevo (`google-genai`); se propuso la migración del cliente y el cambio de modelo a `gemini-3.8-flash`.

**Validación y Corrección Humana:** Antes de aplicar el cambio se verificó en la documentación oficial de Google que el modelo y el paquete sugeridos fueran efectivamente los vigentes, en lugar de confiar en el nombre. Se reconstruyó la imagen de Docker para confirmar que la nueva dependencia quedara instalada y se probó en local antes de dar el fix por válido.

---

## 4. Resiliencia ante fallas y timeouts de la API de IA

**Problema abordado:** Un ticket con contenido que generó una respuesta lenta de Gemini provocó un `WORKER TIMEOUT` en Gunicorn, abortando la request completa y evitando que el ticket se creara.

**Prompt / Herramienta utilizada:** Se consultó a Claude cómo manejar la latencia o indisponibilidad de una API externa dentro de una request síncrona de Django.

**Código / Arquitectura generada:** La primera propuesta fue un bucle de reintentos con espera fija (`sleep`) entre cada intento ante errores temporales (por ejemplo, un 503 de "alta demanda").

**Validación y Corrección Humana:** Esa primera solución resultó insuficiente: al probarla, el tiempo acumulado entre los reintentos propios y los reintentos internos del SDK de Gemini podía superar el límite de 30 segundos de Gunicorn, provocando el mismo `WORKER TIMEOUT` que se buscaba evitar. Se identificó esta ineficiencia de la propuesta inicial y se corrigió reemplazando el enfoque por un timeout duro (vía `ThreadPoolExecutor`, 8 segundos) que garantiza que la vista nunca espera más de un tiempo acotado, devolviendo la prioridad por defecto (`Media`) si la IA no responde a tiempo.

---

*Este registro se actualiza a medida que avanza el desarrollo del proyecto.*