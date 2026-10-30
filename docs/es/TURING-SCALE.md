# Primer patch: Turing Machine → Scale Quantizer

Tu primer patch con dos módulos de G1-Mods. La **Turing Machine** repite en bucle un patrón aleatorio, el
**Scale Quantizer** ajusta ese patrón a una escala musical, y un oscilador toca el resultado.

Necesitas un build con esos dos módulos marcados (el constructor los marca por defecto), funcionando en
G1-Emu o en un G1 real. El patch terminado es
[`patches/turing-scale.pch`](https://raw.githubusercontent.com/animatek/G1-Mods/main/patches/turing-scale.pch):
ábrelo en Animatek NME, o constrúyelo a mano más abajo.

## Qué hace el patch

```
ClkGen ─clock─▶ TuringMachine ─cv─▶ ScaleQuant ─pitch─▶ OscA ─▶ 4Output
```

- **ClkGen** marca el reloj de la Turing Machine desde su salida *4 pulses / beat*.
- El **CV** de la Turing Machine son los 8 bits bajos de su registro como un nivel: un valor que avanza en
  cada reloj, se repite en bucle y se puede dejar a la deriva.
- El **Scale Quantizer** lleva ese valor a la nota más cercana de una escala (aquí Do, escala 1).
- El tono de **OscA** sigue la nota, y el resultado sale por el **4Output** (las salidas del sinte).

## Constrúyelo a mano

1. Añade un **ClkGen**, una **Turing Machine**, un **Scale Quantizer**, un **OscA** y un **4Output**.
2. Cablea ClkGen *4 pulses / beat* → Turing Machine *clock*.
3. Cablea Turing Machine *cv* → Scale Quantizer *in*.
4. Cablea Scale Quantizer *out* → OscA *pitch 1*.
5. Cablea OscA *out* → entrada 1 del 4Output.
6. Pon el **pitch mod 1** de OscA en 127 (una unidad de control es entonces un semitono) y el **freq
   coarse** en la nota base que quieras.

## Qué probar

- **Prob** en la Turing Machine: a la derecha (127) el patrón se repite en bucle; en el centro va a la
  deriva; a la izquierda cambia casi todos los bits.
- **Lock** mantiene el patrón exactamente como está ahora.
- **Scale** (Turing Machine) doma el rango del CV; **Root**, **Scale** y **Octave** (Scale Quantizer)
  eligen la tonalidad y la octava.
- Las **gate 1–8** de la Turing Machine son un bit del patrón cada una: úsalas para disparar envolventes o
  percusión.

El oscilador zumba y recorre notas de la escala a medida que cambia el patrón. Para que suene como un
instrumento, añade la Note del teclado a OscA (o dispara una envolvente AD con una gate de la Turing). El
**8Counter** y el **Address Sequencer** son el siguiente paso: mira la guía de Reloj y reset.
