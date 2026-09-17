#!/bin/bash

set -euo pipefail

# ==============================
# Informations générales
# ==============================

HOSTNAME=$(hostname)
UPTIME=$(uptime -p)
LOAD=$(awk '{print $1" "$2" "$3}' /proc/loadavg)

# ==============================
# CPU
# ==============================

CPU_USAGE=$(top -bn1 | awk '/Cpu\(s\)/ {
    printf "%.1f", 100 - $8
}')

# ==============================
# Mémoire
# ==============================

MEMORY=$(free -m | awk '/Mem:/ {
    printf "{\"total\":%d,\"used\":%d,\"free\":%d,\"percent\":%.1f}",
    $2, $3, $4, ($3 / $2) * 100
}')

# ==============================
# Disque
# ==============================

DISK=$(df -Pm / | awk 'NR==2 {
    gsub("%", "", $5)
    printf "{\"total\":%d,\"used\":%d,\"available\":%d,\"percent\":%d}",
    $2, $3, $4, $5
}')

# ==============================
# Utilisateurs système
# ==============================

USERS="["

FIRST_USER=true

while IFS=: read -r username _ uid gid _ home shell; do

    # On récupère uniquement les utilisateurs humains
    if [ "$uid" -ge 1000 ] && [ "$uid" -lt 60000 ]; then

        if [ "$FIRST_USER" = false ]; then
            USERS+=","
        fi

        USERS+="{\"login\":\"$username\",\"uid\":$uid,\"home\":\"$home\",\"shell\":\"$shell\"}"

        FIRST_USER=false
    fi

done < /etc/passwd

USERS+="]"

# ==============================
# Processus par utilisateur
# ==============================

PROCESSES="["

FIRST_PROCESS=true

while read -r username cpu mem pid command; do

    if [ "$FIRST_PROCESS" = false ]; then
        PROCESSES+=","
    fi

    # Échappement minimal pour JSON
    command=${command//\\/\\\\}
    command=${command//\"/\\\"}

    PROCESSES+="{\"user\":\"$username\",\"cpu\":$cpu,\"memory\":$mem,\"pid\":$pid,\"command\":\"$command\"}"

    FIRST_PROCESS=false

done < <(
    ps -eo user=,pcpu=,pmem=,pid=,comm= --sort=-pcpu |
    head -n 21 |
    awk '{
        printf "%s %.2f %.2f %s %s\n", $1, $2, $3, $4, $5
    }'
)

PROCESSES+="]"

# ==============================
# Résultat JSON
# ==============================

cat <<EOF
{
    "hostname": "$HOSTNAME",
    "uptime": "$UPTIME",
    "load_average": "$LOAD",
    "cpu_percent": $CPU_USAGE,
    "memory": $MEMORY,
    "disk": $DISK,
    "users": $USERS,
    "processes": $PROCESSES
}
EOF
