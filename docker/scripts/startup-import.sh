#!/bin/bash
# startup-import.sh
# Script to import templates from proof-environment/data/templates
# Run this after PROOF is started: ./scripts/startup-import.sh

set -e

# Source common utility functions
SCRIPT_DIR="$(dirname "$(realpath "$0")")"
source "$SCRIPT_DIR/common.sh"

# Configuration
IMPORTER_URL="${IMPORTER_URL:-http://localhost:8090/v1/import}"
TEMPLATES_DIR="${TEMPLATES_DIR:-../data/templates}"
WORKFLOWS_DIR="${WORKFLOWS_DIR:-../data/workflows}"
WAIT_TIMEOUT="${WAIT_TIMEOUT:-180}"
IMPORT_TIMEOUT="${IMPORT_TIMEOUT:-300}"
ENABLE_OVERWRITE="${ENABLE_OVERWRITE:-false}"
CONFIG_MANAGER_URL="${CONFIG_MANAGER_URL:-http://localhost:8100}"
ENABLE_TIME_MEASUREMENT="${ENABLE_TIME_MEASUREMENT:-false}"

echo "=================================================="
echo "PROOF Import Script"
echo "=================================================="
echo "Importer URL: $IMPORTER_URL"
echo "Templates directory: $TEMPLATES_DIR"
echo "Workflows directory: $WORKFLOWS_DIR"
echo "ENABLE_OVERWRITE: $ENABLE_OVERWRITE"
echo ""

# --- Timing measurement ---
if [ "$ENABLE_TIME_MEASUREMENT" = "true" ]; then
    start_time=$(date +%s%N) # nanosecond timestamp at script-start of waiting phase
    echo "start_time: $(date '+%Y-%m-%d %H:%M:%S.%3N')"
fi

# Wait for proof-config-manager to become responsive
if ! wait_for_config_manager "$CONFIG_MANAGER_URL" "$WAIT_TIMEOUT" "STARTUP-IMPORT"; then
    exit 1
fi

if [ "$ENABLE_TIME_MEASUREMENT" = "true" ]; then
    config_manager_ready_time=$(date +%s%N)
    elapsed_config_ms=$(( (config_manager_ready_time - start_time) / 1000000 ))
    echo "curr_time: $(date '+%Y-%m-%d %H:%M:%S.%3N') => waiting took ${elapsed_config_ms} ms"
fi

# Wait for proof-importer REST API to become responsive
if ! wait_for_proof_importer "$IMPORTER_URL" "$WAIT_TIMEOUT" "STARTUP-IMPORT"; then
    exit 1
fi

# Check whether the PROOF database currently contains any templates or workflows.
# Returns 0 (true) only if both are empty; falls back to "not empty" if the check itself fails,
# so reference checks default to the safer "true" behavior.
is_db_empty() {
    local templates
    local workflows

    templates=$(curl -s -m 5 "${CONFIG_MANAGER_URL}/v1/template" 2>/dev/null) || return 1
    workflows=$(curl -s -m 5 "${CONFIG_MANAGER_URL}/v1/workflow" 2>/dev/null) || return 1

    [ "$templates" = "[]" ] && [ "$workflows" = "[]" ]
}

echo "[STARTUP-IMPORT] Checking if PROOF database is empty..."
DEFAULT_CHECK_REFERENCES="true"
if is_db_empty; then
    echo "[STARTUP-IMPORT] Database is empty - disabling reference checks by default"
    DEFAULT_CHECK_REFERENCES="false"
else
    echo "[STARTUP-IMPORT] Database already contains data - reference checks enabled by default"
fi

if [ "$ENABLE_TIME_MEASUREMENT" = "true" ]; then
    importer_ready_time=$(date +%s%N)
    elapsed_total_ms=$(( (importer_ready_time - start_time) / 1000000 ))
    echo "curr_time: $(date '+%Y-%m-%d %H:%M:%S.%3N') => total waiting took ${elapsed_total_ms} ms"
fi

echo ""
echo "[STARTUP-IMPORT] =================================================="

# Global variables to store import results from the last import_files call
LAST_IMPORT_ERROR_COUNT=0
LAST_IMPORT_SUCCESS_COUNT=0
LAST_IMPORT_ID_EXISTS_COUNT=0

# Function to import files (templates or workflows)
# Arguments:
#   $1 - Directory path containing the JSON files
#   $2 - Type name for logging (e.g., "template", "workflow")
#   $3 - Container path prefix (e.g., "/proof/templates", "/proof/workflows")
#   $4 - API endpoint path (e.g., "template", "workflow")
#   $5 - Check references flag (optional, defaults to true)
# Sets global variables: LAST_IMPORT_ERROR_COUNT, LAST_IMPORT_SUCCESS_COUNT, LAST_IMPORT_ID_EXISTS_COUNT
import_files() {
    local dir_path="$1"
    local type_name="$2"
    local container_prefix="$3"
    local api_endpoint="$4"
    local check_references="${5:-true}"
    
    local count=0
    local error_count=0
    local success_count=0
    local id_exists_count=0
    
    if [ ! -d "$dir_path" ]; then
        echo "[STARTUP-IMPORT] ERROR: ${type_name^} directory not found at $dir_path"
        return 1
    fi
    
    local files=$(find "$dir_path" -maxdepth 1 -name "*.json" | sort)
    local total=$(echo "$files" | grep -c . || echo 0)
    
    if [ $total -eq 0 ]; then
        echo "[STARTUP-IMPORT] No ${type_name} files found in $dir_path"
        return 0
    fi
    
    echo "[STARTUP-IMPORT] Found $total ${type_name} file(s) to import..."
    echo ""
    
    for file in $files; do
        local file_name=$(basename "$file")
        count=$((count + 1))
        
        echo -n "[STARTUP-IMPORT]   [$count/$total] Importing $file_name... "
        
        local container_path="${container_prefix}/${file_name}"
        local api_url="$IMPORTER_URL/${api_endpoint}?${api_endpoint}Path=${container_path}&save=true&overwrite=$ENABLE_OVERWRITE&checkReferences=$check_references"
        
        if response=$(curl -s -m $IMPORT_TIMEOUT -X POST "$api_url" 2>&1); then
            if echo "$response" | grep -q '"status":"ERROR"'; then
                echo -n "✗ ERROR"
                # Extract and display the error output from the response
                error_output=$(echo "$response" | grep -o '"output":"[^"]*"' | sed 's/"output":"//;s/"$//')
                if [ -n "$error_output" ]; then
                    echo ": $error_output"
                else
                    echo ""
                fi
                error_count=$((error_count + 1))
            elif echo "$response" | grep -q '"status":"IMPORT_SUCCESS"'; then
                echo "✓ IMPORT_SUCCESS"
                success_count=$((success_count + 1))
            else
                # ID already exists
                echo "- ID_EXISTS"
                id_exists_count=$((id_exists_count + 1))
            fi
        else
            echo "✗ ERROR (curl failed)"
            error_count=$((error_count + 1))
        fi
    done
    
    echo ""
    echo "[STARTUP-IMPORT] $total ${type_name^} import complete:"
    echo "[STARTUP-IMPORT]   IMPORT_SUCCESS: $success_count"
    echo "[STARTUP-IMPORT]   ID_EXISTS: $id_exists_count"
    echo "[STARTUP-IMPORT]   ERROR: $error_count"
    
    # Set global variables for caller to access
    LAST_IMPORT_ERROR_COUNT=$error_count
    LAST_IMPORT_SUCCESS_COUNT=$success_count
    LAST_IMPORT_ID_EXISTS_COUNT=$id_exists_count
    
    if [ $error_count -gt 0 ]; then
        echo "[STARTUP-IMPORT] WARNING: $error_count ${type_name}(s) failed to import"
        return 1
    fi
    
    return 0
}

# Import templates
# Remark: Template import overwrites Programs and Attachments
echo "[STARTUP-IMPORT] Importing templates..."
echo ""
template_result=0
import_files "$TEMPLATES_DIR" "template" "/proof/templates" "template" "$DEFAULT_CHECK_REFERENCES" || template_result=$?

# Capture template import results
template_error_count=$LAST_IMPORT_ERROR_COUNT
template_success_count=$LAST_IMPORT_SUCCESS_COUNT
template_id_exists_count=$LAST_IMPORT_ID_EXISTS_COUNT

# When all templates were imported, we know that the program and attachment references fit the 
# workflow reference and we accept that there are references already.
# Remark: Ideally we would need to check only for the respectve workflow templates.
check_workflow_references="$DEFAULT_CHECK_REFERENCES"
if [ $template_error_count -eq 0 ] && [ $template_id_exists_count -eq 0 ]; then
    check_workflow_references="false"
fi

echo "[STARTUP-IMPORT] ========================"
echo "[STARTUP-IMPORT] Importing workflows..."
echo ""

# Import workflows
workflow_result=0
import_files "$WORKFLOWS_DIR" "workflow" "/proof/workflows" "workflow" $check_workflow_references || workflow_result=$?

# Capture workflow import results
workflow_error_count=$LAST_IMPORT_ERROR_COUNT
workflow_success_count=$LAST_IMPORT_SUCCESS_COUNT
workflow_id_exists_count=$LAST_IMPORT_ID_EXISTS_COUNT

echo "[STARTUP-IMPORT] =================================================="

# Exit with error if any imports failed (only ERROR status counts as failure)
if [ $template_result -ne 0 ] || [ $workflow_result -ne 0 ]; then
    echo "[STARTUP-IMPORT] ERROR: Some imports failed"
    exit 1
else
    echo "[STARTUP-IMPORT] All imports complete"
fi

exit 0
