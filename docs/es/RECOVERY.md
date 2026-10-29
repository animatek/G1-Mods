# Volver atrás y soluciones

El modo update vive en el chip de ROM del G1, que nada de lo de aquí puede escribir. Tenga lo que tenga la
flash, **Shift + Store** al encender llega hasta él.

## Volver al OS de Clavia

1. Borra o sobrescribe los patches guardados que usen módulos nuevos (mira la guía de instalación).
2. Apaga el G1. **Mantén pulsados Shift + Store y enciéndelo.**
3. Instala el OS de Clavia, a la velocidad segura (más lenta), por la misma interfaz MIDI, de una de estas
   dos maneras:
    - **El *Device > Update Synth OS* de NME**, eligiendo **la imagen del OS 3.03b de Clavia** (un `.bin`,
      que es lo que necesita NME: no lee el actualizador de Clavia). Consíguela antes de flashear nada:
      G1-Emu guarda el OS que recibe en su carpeta `os` después de pasarle el actualizador de Clavia, y
      `tools/g1update.py unpack` convierte una actualización grabada (`.syx`) en la misma imagen. Guárdala
      con tus copias de seguridad: es de Clavia, así que no la compartas.
    - **El propio actualizador del OS 3.03b de Clavia** (el `.exe` de Windows, o la versión de Mac; en
      Linux funciona con Wine).
4. Pulsa **Store** en «Update flash?», espera a *Update completed*, apágalo y enciéndelo.

**Shift + Patch/Load** al encender arranca el OS de fábrica de la ROM, nunca el de la flash: una forma de
usar el sinte mientras lo arreglas.

## Si algo sale mal

| Lo que ves | Qué significa | Qué hacer |
| --- | --- | --- |
| *Writing to flash / Write Error* | No se pudo escribir la flash. | Apaga y enciende: vuelve solo al modo update. Instala el 3.03b de Clavia (más arriba). |
| *Update utility / Curr ver 255.255* en un encendido normal | La flash no tiene OS (una actualización que falló a medias). | Instala un OS: el tuyo otra vez, o el 3.03b de Clavia. |
| Muestra su nombre y versión y se queda ahí | El OS se instaló pero no arranca. | Shift + Store al encender e instala el 3.03b de Clavia. Avísanos (más abajo). |
| No sale *Update utility* con Shift + Store | No se mantuvieron las teclas desde el principio. | Mantén las dos antes de encender, hasta que cambie la pantalla. |

## Avisar de un problema

Abre un [issue](https://github.com/animatek/G1-Mods/issues) con: la lista de módulos del build, si fue
G1-Emu o un G1 real, qué mostraba la pantalla y qué hiciste justo antes. No hay soporte para hardware real
ni promesa de arreglo (README, «Who is responsible for what»), pero cada aviso ayuda.
