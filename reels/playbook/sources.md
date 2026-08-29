# Fuentes que se revisan antes de cada Reel

El sistema no inventa el tema del dia: lo busca. Este es el orden de revision,
de mas a menos autoritativo. Basta con encontrar **un** hallazgo publicado en
los ultimos 7 dias que aporte algo concreto.

## 1. Datos oficiales (maxima prioridad)

| Fuente | Que aporta | Cadencia |
|---|---|---|
| Statistics Canada — Labour Force Survey (`statcan.gc.ca`, *The Daily*) | Empleo, desempleo, ganancias por industria y provincia | Mensual, primer viernes |
| Statistics Canada — Job Vacancy and Wage Survey | Vacantes y salarios ofrecidos por ocupacion | Trimestral |
| Job Bank Canada (`jobbank.gc.ca`) — Outlooks | Perspectivas por ocupacion y provincia, salarios medianos | Continuo |
| IRCC / Express Entry / PNP | Cambios de permisos de trabajo y vias provinciales | Irregular |
| Bank of Canada — Business Outlook Survey | Intencion de contratacion de los empleadores | Trimestral |

## 2. Analisis de mercado

- Indeed Hiring Lab Canada — lectura del LFS y de las ofertas publicadas.
- Robert Half Canada / Adecco / Randstad — demanda por rol y rangos salariales.
- LinkedIn Economic Graph y reportes de Jobs on the Rise.

## 3. Senal de industria

- Anuncios de contratacion, aperturas y expansiones de empleadores en Canada.
- Cambios de politica de trabajo remoto o regreso a la oficina.
- Noticias sobre uso de AI en seleccion de personal.

## Reglas de uso

1. **Solo se cita lo verificado.** Cada cifra que sale en pantalla queda
   registrada en `sources.md` del Reel con enlace directo a la fuente
   primaria. Si un dato no se puede enlazar, no se publica.
2. **Frescura.** Se prefiere lo publicado en los ultimos 7 dias. Hasta 30 dias
   sirve si se etiqueta con el mes al que corresponde ("datos de julio").
3. **Nunca se redondea a favor del gancho.** Si el dato es +75.000, se dice
   +75.000, no "casi 100.000".
4. **El dato se traduce a consecuencia.** Un numero sin "y esto significa para
   ti que..." no es un Reel, es una noticia.
5. **Si no hay nada suficientemente relevante**, se cae a un tema evergreen de
   la rueda (`topics.json`, categorias con `newsDriven: false`) y se marca el
   Reel con `"evergreen": true`. No se fuerza una noticia debil.
