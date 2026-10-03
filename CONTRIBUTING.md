cat > CONTRIBUTING.md << 'XARION_EOF'
# Guia de Contribucion

Gracias por tu interes en contribuir a XARION 1.0.

Este documento describe como reportar errores, proponer mejoras y
enviar cambios al proyecto.

## Codigo de conducta

- Se respetuoso con otros contribuidores.
- Acepta criticas constructivas.
- Enfocate en lo tecnico, no en lo personal.
- Reporta problemas de forma clara y con evidencia.

## Como reportar un bug

Antes de abrir un issue:

1. Verifica que no exista ya un issue con el mismo problema.
2. Comprueba que usas la ultima version del proyecto.
3. Revisa la documentacion en `docs/`.

Al abrir un issue incluye:

- Version de XARION (`python main.py --status`).
- Version de Python (`python --version`).
- Sistema operativo y distribucion.
- Descripcion clara del problema.
- Pasos para reproducirlo.
- Comportamiento esperado vs comportamiento observado.
- Logs o mensajes de error completos.
- Capturas o video si aplica.

## Como proponer una mejora

Abre un issue con la etiqueta `enhancement` y describe:

- Que problema resuelve.
- Como lo haria actualmente el usuario.
- Como deberia funcionar la mejora.
- Impacto en el resto del sistema.
- Alternativas consideradas.

## Como enviar un Pull Request

### 1. Prepara tu entorno

```bash
git clone https://github.com/Erhik-jhan/XARION1.0.git
cd XARION1.0
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"