# Reloj y reset

Los secuenciadores y los contadores siguen todos el mismo reloj, y el **reset** es lo que los mantiene en el
mismo paso. Esta guía cubre la señal de reloj, cómo funciona el reset en los secuenciadores propios del G1 y
en el **Address Sequencer** y el **8Counter** de G1-Mods, y los patches que lo muestran.

## El reloj

Un reloj es una gate regular. **ClkGen** hace uno (sus salidas *4 pulses / beat* y *24 pulses / beat*); los
secuenciadores del G1, el Address Sequencer y el 8Counter avanzan un paso con cada flanco de subida.

## Reset

El reset funciona igual en los secuenciadores propios del G1 y en los módulos de G1-Mods:

- El flanco de **Rst** arma el módulo, y **el siguiente reloj** va al paso 1.
- El módulo **empieza en su último paso**, así que el primer reloj toca el paso 1.
- Eso es lo que mantiene varios módulos **a compás**: dales el mismo reloj y el mismo reset, y caerán juntos
  en el paso 1.

Así que para empezar cada compás en el paso 1, manda un flanco de reset a cada secuenciador y contador,
justo antes del primer reloj.

## El patch: un Address Sequencer y un CtrlSeq juntos

[`modules/step-seq-5/seq5-ctrlseq.pch`](https://raw.githubusercontent.com/animatek/G1-Mods/main/modules/step-seq-5/seq5-ctrlseq.pch)
lo muestra: un ClkGen marca el reloj de un **Address Sequencer** y de un **CtrlSeq** del G1, y un flanco de LFOA
reinicia los dos. Se quedan en el mismo paso.

[`modules/counter8/counter8.pch`](https://raw.githubusercontent.com/animatek/G1-Mods/main/modules/counter8/counter8.pch)
hace lo mismo con el **8Counter**: sus ocho salidas están altas de una en una, a compás con el reloj y el
reset.

## Qué probar

- Cambia el **rate** del ClkGen para acelerarlo todo a la vez.
- Ajusta los cinco pomos del Address Sequencer y escucha el patrón.
- Usa las ocho salidas del 8Counter como las gates de ocho eventos: cada una se dispara por turno.
- Marca el reloj de un secuenciador largo y de uno corto desde la misma fuente y con el mismo reset: el corto
  da la vuelta cada compás mientras el largo sostiene la frase.
