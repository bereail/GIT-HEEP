#!/bin/sh
# Trae a esta PC la última copia diaria de la base del servidor y deja las 30
# más nuevas. Lo corre una tarea programada de Windows (ver CLAUDE.md).
set -eu
DESTINO="/d/Bere/Copias/timbo-capacitaciones"
SSH="ssh -i $HOME/.ssh/timboheep_ed25519 -p5440 -o BatchMode=yes root@138.36.238.175"
mkdir -p "$DESTINO"
ULTIMA=$($SSH 'ls -1t /var/www/timbo-capacitaciones/copias/centro_aprendizaje-*.sqlite3 | head -1')
scp -q -i "$HOME/.ssh/timboheep_ed25519" -P 5440 -o BatchMode=yes "root@138.36.238.175:$ULTIMA" "$DESTINO/"
ls -1t "$DESTINO"/centro_aprendizaje-*.sqlite3 | tail -n +31 | while read -r viejo; do rm -f "$viejo"; done
echo "$(date '+%d/%m/%Y %H:%M') copia: $(basename "$ULTIMA")" >> "$DESTINO/registro.txt"
