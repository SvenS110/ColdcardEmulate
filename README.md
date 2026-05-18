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

## Licencia

Este proyecto se distribuye bajo GPL-3.0.

Coldcard firmware es un proyecto externo con su propia licencia. Esta herramienta no redistribuye el firmware; lo clona desde su repositorio oficial para uso local de laboratorio.
