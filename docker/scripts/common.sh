#!/bin/bash
# common.sh
# Shared utility functions for startup scripts

# Function to wait for a service to become responsive
# Arguments:
#   $1 - service_name: Name of the service for logging
#   $2 - check_command: Command to run to check service status
#   $3 - expectedResponse: Expected output from check command
#   $4 - prefix_override: (optional) Overrides the log prefix for this wait operation
wait_for_service() {
    local service_name="$1"
    local check_command="$2"
    local expectedResponse="$3"
    local prefix_override="$4"
    
    # Wait message stays on screen; the elapsed-seconds counter is printed
    # right after it on the same line and updated in place each second.
    local prefix="[${prefix_override:-STARTUP}]"
    local msg="$prefix Waiting for $service_name..."
    echo -n "$msg"
    
    local WAIT_TIME=0
    while [ $WAIT_TIME -lt $WAIT_TIMEOUT ]; do
        serviceIsUp=$(${check_command[@]})
        if [ "$serviceIsUp" = "$expectedResponse" ]; then
            echo -e "\n$prefix ✓ $service_name is ready"
            return 0
        fi
        WAIT_TIME=$((WAIT_TIME + 1))
        # \r = back to column 0, \033[K = clear to end of line
        printf "\r\033[K%s %ss" "$msg" "$WAIT_TIME"
        sleep 1
    done
    
    echo ""
    echo "$prefix ERROR: Timed out waiting for $service_name after $WAIT_TIMEOUT seconds"
    echo "$prefix Make sure PROOF is running: startPROOF -D"
    return 1
}

# Function to wait for config-manager to be ready
# Arguments:
#   $1 - config_manager_url: URL of the config-manager service
#   $2 - timeout: (optional) Timeout in seconds, defaults to WAIT_TIMEOUT or 180
#   $3 - prefix: (optional) Log prefix, defaults to STARTUP
wait_for_config_manager() {
    local config_manager_url="$1"
    local timeout="${2:-${WAIT_TIMEOUT:-180}}"
    local prefix="$3"
    
    local original_wait_timeout=$WAIT_TIMEOUT
    WAIT_TIMEOUT=$timeout
    
    local health_check_cmd=("curl -s -m 2 ${config_manager_url}/actuator/health")
    local expected_response="{\"status\":\"UP\"}"
    
    wait_for_service "proof-config-manager at ${config_manager_url}" "${health_check_cmd}" "$expected_response" "$prefix"
    local result=$?
    
    WAIT_TIMEOUT=$original_wait_timeout
    return $result
}

# Prints "up" if proof-importer answers on /template (used as a wait_for_service check)
_proof_importer_check() {
    if curl -s -m 5 -X POST "$1/template" 2>/dev/null | grep -q .; then
        echo "up"
    fi
}

# Function to wait for proof-importer to be ready
# Arguments:
#   $1 - importer_url: URL of the importer service
#   $2 - timeout: (optional) Timeout in seconds, defaults to WAIT_TIMEOUT or 180
#   $3 - prefix: (optional) Log prefix, defaults to STARTUP
wait_for_proof_importer() {
    local importer_url="$1"
    local timeout="${2:-${WAIT_TIMEOUT:-180}}"
    local prefix="$3"
    
    local original_wait_timeout=$WAIT_TIMEOUT
    WAIT_TIMEOUT=$timeout
    
    wait_for_service "proof-importer at ${importer_url}" "_proof_importer_check ${importer_url}" "up" "$prefix"
    local result=$?
    
    WAIT_TIMEOUT=$original_wait_timeout
    return $result
}
