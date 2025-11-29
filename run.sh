#!/usr/bin/with-contenv bashio

ARGS=(
    python3
    -m
    lt2ha.bridge
    lt2ha-addon
)

add_arg() {
    local PARAM="--${1//_/-}"
    local VALUE

    for VALUE in $(bashio::config "$1"); do
        if [[ -n "$VALUE" ]]; then
            ARGS+=("$PARAM" "$VALUE")
        fi
    done
}

add_arg ha_mqtt_discovery_prefix
add_arg mqtt_host
add_arg mqtt_port
add_arg mqtt_username
add_arg mqtt_password
add_arg mqtt_proto
add_arg mqtt_transport
add_arg lt_host
add_arg lt_port
add_arg lt_key
add_arg lt_ignore_addr
add_arg lt_ignore_type
add_arg lt_ignore_area

exec "${ARGS[@]}"
