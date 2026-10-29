# Instalar G1-Mods

Cómo meter los módulos nuevos en **G1-Emu** y en un **rack Nord Modular G1 real**, paso a paso.
Léelo entero una vez antes de empezar, y mira la vuelta atrás (`docs/RECOVERY.md`) antes de tocar un
sinte real.

> **Experimental.** En un G1 real (2026-10-26) los 13 módulos han sonado en un mismo build, y volver
> al OS de Clavia funcionó todas las veces. Eso es un solo sinte. Un OS modificado todavía puede borrar
> tus patches o dejar tu G1 inservible, y la recuperación no está garantizada. Lo haces bajo tu propia
> responsabilidad; eres responsable de tu instrumento. Prueba todo primero en G1-Emu.

## Dos archivos, dos maneras de entrar

El constructor da dos archivos. **No son intercambiables**; esta es toda la diferencia:

| Archivo | Para | Cómo se carga |
| --- | --- | --- |
| **Actualización de OS** (`g1mods-...-os.bin`) | **G1-Emu y un G1 real** | **Solo mediante el modo update**, igual en los dos: pon el sinte en modo update y luego usa *Device > Update Synth OS* de NME. En G1-Emu: *Settings > OS... > Update mode*. En un G1 real: Shift + Store pulsados al encender. |
| **ROM** (`g1mods-...-rom.bin`) | **Solo G1-Emu** | En *Settings > ROM > Choose...* de G1-Emu; ofrece reiniciar con ella. Un G1 real no puede cogerla, y el Update Synth OS de NME la rechaza (son 512 KB y una actualización tiene sitio para 393.184 bytes). |

Si dudas, usa la actualización de OS: funciona en los dos. La ROM es solo un atajo para el emulador.

## Lo que necesitas

- **La ROM 3.03 del rack**, el archivo que arranca G1-Emu (`NORD-MODULAR-RACK-VER-3.03.BIN`, 512 KB). No la
  damos: es de Clavia. Los módulos se construyen sobre tu propia copia.
- **Animatek NME 0.25 o posterior**: la primera versión con soporte de G1-Mods. Enseña los módulos nuevos
  cuando un sinte los tiene, y trae *Device > Update Synth OS* para instalar un OS por MIDI. Las versiones
  anteriores no conocen los módulos nuevos: con una, un OS de G1-Mods conecta pero los módulos no se ofrecen.
- **G1-Emu**, para probar un build antes de un sinte real.
- **Un G1 rack o con teclado.** La **Micro Modular** corre otro OS y no tiene ROM: dale al constructor el
  actualizador de la Micro de Clavia (`Nord Micro Modular OS v3.03b Update.exe`, o el zip que lo contiene) en lugar de
  la ROM. Se construyen en él doce de los módulos (no Note Out), como una actualización de OS que funciona en el modelo
  Micro de G1-Emu (*Settings > Micro OS*). **Experimental: nadie lo ha probado en una Micro real**, así que no lo
  instales en una (mira el [roadmap](../ROADMAP.md) y `NOTES.md`).
- Para un G1 real: una interfaz MIDI conectada al **puerto PC** del G1 (en los dos sentidos), como para editar.
- Para la vuelta atrás en un G1 real, cualquiera de estas dos:
    - **El *Device > Update Synth OS* de NME** con **la imagen del OS 3.03b original de Clavia** (un `.bin`):
      igual que instalaste el tuyo, con el G1 en modo update. Guarda esa imagen antes de empezar (mira
      *Volver atrás y soluciones*);
    - o **el actualizador del OS 3.03b de Clavia** (el `.exe` de Windows, o la versión de Mac; en Linux
      funciona con Wine).

## 1. Construye tu OS

En la página del constructor (en la web publicada, o `web/serve.sh` desde un clon):

1. Suelta tu ROM 3.03 en ella. Comprueba que es la correcta. No se sube nada.
2. Marca los módulos que quieras.
3. Marca que has leído los riesgos y pulsa **Construir mi OS**.
4. Obtienes **un archivo, la actualización de OS** (`g1mods-...-os.bin`), y sirve para los dos: instálalo
   en G1-Emu (en modo update) o en la flash de un G1 real, de la misma manera, con *Device > Update Synth OS*
   de NME. La página también da la ROM entera (`g1mods-...-rom.bin`), solo para G1-Emu: NME la rechaza por
   demasiado grande para una actualización. Si no hay actualización de OS (demasiados módulos, o un módulo
   que por ahora solo funciona en G1-Emu; un build solo para G1-Emu está en el [roadmap](../ROADMAP.md)),
   la página dice por qué y la ROM es el único archivo.

Desde un clon de este repo, lo mismo es `tools/patch_rom.py` y `tools/g1update.py fromrom`
(README, «Where the builds are»).

Guarda tu lista de módulos, no los archivos: los archivos contienen el firmware de Clavia y no deben
compartirse. Cualquiera con su propia ROM construye el mismo OS con la misma lista.

## 2. Pruébalo en G1-Emu

**Con la actualización de OS (lo habitual, igual que en un G1 real):** pon G1-Emu en modo update
(*Settings > OS... > Update mode*), luego en NME *Device > Update Synth OS*, elige el `…-os.bin` y empieza.
Cuando termina, G1-Emu se queda con ese OS. Sigue después con «Sea cual sea» más abajo.

**O con la ROM** (`g1mods-...-rom.bin`): en G1-Emu, *Settings > ROM > Choose...*; ofrece reiniciar con ella
(un G1-Emu anterior al 2026-10-29 solo la apunta: ciérralo y ábrelo otra vez). Se usa entonces tu flash de
siempre, así que los patches que nombran un módulo nuevo conviene guardarlos en una flash aparte. Desde un
clon, `./run-g1emu.sh` construye la ROM y arranca G1-Emu con ella y **una flash propia**.

Si los ajustes de G1-Emu nombran un archivo de OS (`os =`, que deja una actualización anterior), ese OS
arranca en lugar del de la ROM y los módulos no están: *Settings > OS... > The ROM's own OS* lo borra
(`./run-g1emu.sh` arranca con `G1_OS=` vacío por el mismo motivo).

Sea cual sea:

1. Conecta NME. Dice **MODDED OS** en su barra de estado, el sinte informa de la versión **3.09** y los
   módulos nuevos están en la paleta de módulos.
2. Carga un patch que los use (la carpeta de cada módulo tiene uno, `modules/<nombre>/*.pch`).

## 3. Instálalo en un G1 real

Hazlo en orden. La actualización entera tarda unos **12 minutos** a la velocidad segura.

1. **Haz copia de tus patches.** En NME, guarda en tu ordenador cada banco que te importe.
2. **Comprueba con qué sinte habla NME**: el G1 real, no G1-Emu.
3. **Apaga el G1. Mantén pulsados Shift + Store y enciéndelo.** Muestra *Update utility* y espera.
4. En NME: **Device > Update Synth OS**. Elige el archivo de **actualización de OS** (`g1mods-...-os.bin`),
   velocidad **Safe**, y empieza.
5. Déjalo en paz hasta que termine: no toques el cable, el sinte ni el ordenador.
6. El G1 pregunta **«Update flash?»**: pulsa **Store**. Cualquier otra tecla conserva tu OS anterior.
   Muestra *Erasing flash*, *Writing to flash*, *Verifying flash* y luego *Update completed*.
7. **Apágalo y enciéndelo.** Arranca como siempre.
8. Conecta NME: **MODDED OS** en la barra de estado, y los módulos nuevos en la paleta.

### Usar los módulos

- Toca patches con módulos nuevos **en un slot**. Guardar uno en un banco funciona con el OS modificado,
  pero bajo el OS de Clavia ese patch nombra un módulo que el OS no tiene, y cargarlo puede colgar el
  sinte. **Antes de volver al OS de Clavia, borra o sobrescribe todos los patches guardados que usen un
  módulo nuevo.**
- Un patch con un módulo nuevo solo se puede enviar a un sinte cuyo OS tenga ese módulo: NME lo comprueba.
