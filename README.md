# ColdcardEmulate

CLI en Python para instalar, preparar, compilar y ejecutar el simulador de Coldcard.

Modelos soportados:

- mk4
- mk5
- q1

## Requisitos

- Linux o WSL
- git
- python3
- make
- apt (para `install`)

## Uso rápido

```bash
python3 coldcard_emulate.py check
python3 coldcard_emulate.py all --model mk4
```

## Uso por pasos

```bash
python3 coldcard_emulate.py check
python3 coldcard_emulate.py install
python3 coldcard_emulate.py clone
python3 coldcard_emulate.py build
python3 coldcard_emulate.py run --model mk4
```

## Ejemplos por modelo

```bash
python3 coldcard_emulate.py run --model mk4
python3 coldcard_emulate.py run --model mk5
python3 coldcard_emulate.py run --model q1
```

## Ejemplo dry-run

```bash
python3 coldcard_emulate.py all --model mk5 --dry-run
```

## Nota de seguridad

Esta herramienta es solo para laboratorio y simulación del firmware de Coldcard.
No gestiona fondos reales, no debe usarse como wallet y no debe confundirse con un dispositivo Coldcard físico.

## Desinstalación completa

1) Cierra cualquier simulador o terminal que lo esté ejecutando.

2) Si usaste la ruta por defecto, elimina el entorno de trabajo con:

```bash
rm -rf ~/coldcard-emulate
```

Advertencia: ese comando borra TODO el contenido de ese directorio. No lo uses si ahí tienes cambios o archivos que quieras conservar.

3) Si ejecutaste la herramienta con `--workdir` y otra ruta, elimina ESA ruta en lugar de `~/coldcard-emulate`.

4) Opcional: si también quieres borrar este repositorio local:

```bash
cd ..
rm -rf ColdcardEmulate
```

Antes de ejecutar `rm -rf`, verifica `pwd` para confirmar que estás en la ubicación correcta.

### Opcional: eliminar dependencias apt instaladas por la herramienta

Hazlo con cuidado. No se recomienda eliminar `git`, `python3`, `python3-pip`, `python3-venv`, `make` ni `build-essential` si los usas en otros proyectos.

En cambio, puedes revisar y eliminar paquetes más específicos si ya no los necesitas:

- `gcc-arm-none-eabi`
- `libudev-dev`
- `libffi-dev`
- `xterm`
- `swig`
- `libpcsclite-dev`
- `autoconf`
- `libtool`
- `libsdl2-dev`
- `libsdl2-image-dev`
- `libsdl2-mixer-dev`
- `libsdl2-ttf-dev`

Comandos de verificación:

```bash
test ! -d ~/coldcard-emulate && echo "Entorno eliminado"
ps aux | grep -i simulator.py
```

## Licencia

Este proyecto se distribuye bajo GPL-3.0.

Coldcard firmware es un proyecto externo con su propia licencia. Esta herramienta no redistribuye el firmware; lo clona desde su repositorio oficial para uso local de laboratorio.
