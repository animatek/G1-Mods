# Conecta Animatek NME a G1-Emu

La entrada segura: prueba cada build y cada patch en **G1-Emu** antes de que nada toque un G1 real. Esto
recorre cómo arrancar G1-Emu con un OS de G1-Mods y conectarle **Animatek NME**.

## Lo que necesitas

- Un build: la ROM del constructor web, o `tools/patch_rom.py` (mira la guía de instalación).
- **G1-Emu**, compilado (el banco de pruebas de este repo).
- **Animatek NME 0.25 o posterior** (la primera con la capa de G1-Mods): ofrece los módulos nuevos a un
  sinte cuyo OS informa de 3.09 al conectar.

## 1. Arranca G1-Emu con el build

Cierra cualquier G1-Emu que ya esté en marcha: los dos cogerían los mismos puertos MIDI. Desde este repo:

```
./run-g1emu.sh
```

Construye la ROM en `Roms/rom-all.bin`, crea su propia flash (tu flash de siempre no se toca nunca) y abre
la ventana de G1-Emu con esa ROM. A mano es lo mismo: arranca G1-Emu con tu ROM construida y una flash de
pruebas.

## 2. Conecta NME

En NME, elige el **PC Port** de G1-Emu como entrada y salida MIDI: el puerto del editor, el mismo que
usarías con un G1 real.

## 3. Lo que deberías ver

- La barra de estado de NME dice **MODDED OS**, y el sinte informa de la versión **3.09**.
- Los módulos nuevos están en la paleta (TuringMachine, ScaleQuant, 5-StepSeq, 8Counter y el resto) bajo su
  propia categoría.

## 4. Abre un patch

Abre
[`patches/turing-scale.pch`](https://raw.githubusercontent.com/animatek/G1-Mods/main/patches/turing-scale.pch)
y oirás el oscilador recorriendo las notas de una escala. Cada carpeta de módulo tiene además un patch
propio (`modules/<nombre>/*.pch`).

Los mismos pasos en un G1 real (más instalar el OS con *Device > Update Synth OS*) están en la guía de
instalación.
