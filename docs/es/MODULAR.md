# El Nord Modular G1

Un sintetizador modular de analógico virtual de Clavia, lanzado en 1998: un rack de chips DSP que se patchea
desde un ordenador, con pomos reales para los parámetros que asignes.

## Qué es

- Construyes el sonido en pantalla a partir de **módulos** (osciladores, filtros, envolventes,
  secuenciadores…) unidos por cables, en un editor.
- El patch corre **dentro del sinte**, en sus DSP, así que sigue sonando sin el ordenador.
- Los pomos, los **morphs** y los controladores MIDI se pueden asignar a cualquier parámetro, y eso lo hace
  tocable.

## Una breve historia

Clavia hizo el Nord Modular como un modular que corre en DSP en vez de en racks de placas analógicas:
diseñas el sonido en software y el hardware lo toca. Clavia se detuvo en 128 tipos de módulo y pasó al Nord
Modular **G2**; el OS del G1 todavía funciona hoy, y sobre eso se apoya G1-Mods.

## Los modelos

- **Keyboard**: las teclas y el panel, en un solo instrumento.
- **Rack**: el que tiene como objetivo G1-Mods. Cuatro DSP, sin teclado, se patchea desde el editor.
- **Micro Modular**: el pequeño, un solo DSP y un panel más reducido.

## Cómo corre un patch

El patch corre **dentro del sinte**, no en el ordenador.

- El rack tiene **cuatro DSP** (el Micro, uno). Un patch se reparte entre ellos como una sola cadena,
  unidos por enlaces de alta velocidad que llevan nueve palabras en cada muestra.
- Los módulos son de **tasa de control** (secuenciadores, envolventes, LFO lentos: se actualizan con menos
  frecuencia, cuestan poco) o de **tasa de audio** (osciladores, filtros: cada muestra). Los primeros módulos
  de G1-Mods son de tasa de control; Osc String es el primero de tasa de audio.
- Lo que sube un editor (Animatek NME, o el de Clavia) es una lista de módulos, sus parámetros y sus cables.
  El OS la reparte en los DSP y la ejecuta.

## Por qué añadir módulos ahora

Clavia se detuvo en 128 tipos de módulo y pasó al G2. El OS del G1 es un programa como cualquier otro: si
sabes dónde se registra un módulo, cuáles son sus parámetros y cómo está organizado su código DSP, puedes
añadir uno. Eso es lo que hace este proyecto, con código escrito de nuevo.

## De un número de tipo a un módulo

1. El OS conoce cada módulo por un **número de tipo**. G1-Mods toma los libres.
2. Registra el módulo: nombre, parámetros, luces, entradas y salidas.
3. Añade el código **DSP56300** del módulo, ensamblado con nuestra propia herramienta.
4. El OS dice **3.09** cuando un editor pregunta. Animatek NME ofrece entonces los paneles nuevos.

## Herramientas alrededor

- [Animatek NME](https://github.com/animatek/Animatek-NME): el editor moderno para el G1, con soporte para
  OS modificados desde la versión 0.25.
- [G1-Emu](https://github.com/animatek/G1-Emu): el G1 corriendo su propio OS, como plugin o programa
  independiente. El banco de pruebas de aquí.
