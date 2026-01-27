#!/usr/bin/env bash
#
# Extended Scalability Experiment Runner
# ======================================
# Orchestrates comprehensive scalability benchmark experiments across
# 5 database systems and 3 scaling dimensions.
#
# Features:
# - Dry-run mode with detailed experiment plan
# - Series selection (run specific series)
# - Resume capability (skips completed experiments)
# - Parallel execution within series
# - Comprehensive logging
# - Signal handling for graceful shutdown
# - Timeout protection
#
# Usage:
#   ./configs/extended_scalability/run_all.sh [OPTIONS]
#
# Options:
#   --dry-run       Show experiment plan without executing
#   --list          Show current status of all experiments
#   --series N      Run only series N (1-5)
#   --resume        Skip already completed experiments
#   --experiment X  Run single experiment by name
#   --no-cleanup    Don't destroy infrastructure after each run
#   --parallel N    Run N experiments concurrently (default: 1)
#   --reset         Reset experiment state
#   --help          Show this help message
#

set -o pipefail

# =============================================================================
# Configuration
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
CONFIG_DIR="${SCRIPT_DIR}"
RESULTS_DIR="${REPO_ROOT}/results"
LOG_DIR="${REPO_ROOT}/logs/extended_scalability"
STATE_FILE="${LOG_DIR}/.experiment_state"

# Series definitions
declare -A SERIES_NAMES=(
    [1]="Node Scaling"
    [2]="Scale Factor Scaling"
    [3]="Stream Scaling (Cluster)"
    [4]="Stream Scaling (Single Node)"
    [5]="Stress Tests"
)

declare -A SERIES_DIRS=(
    [1]="series_1_nodes"
    [2]="series_2_sf"
    [3]="series_3_streams_cluster"
    [4]="series_4_streams_single"
    [5]="series_5_stress"
)

declare -A SERIES_SYSTEMS=(
    [1]="4"  # Exasol, ClickHouse, Trino, StarRocks
    [2]="5"  # All 5 systems
    [3]="4"  # Cluster-capable only
    [4]="5"  # All 5 systems
    [5]="4"  # Cluster-capable only
)

# Series enabled by default (1=enabled, 0=disabled)
declare -A SERIES_ENABLED=(
    [1]="1"
    [2]="1"
    [3]="0"  # Disabled: Cluster stream scaling (expensive)
    [4]="1"
    [5]="0"  # Disabled: Stress tests (expensive)
)

# Experiment configs by series
declare -a SERIES_1_CONFIGS=("nodes_1" "nodes_4" "nodes_8" "nodes_16")
declare -a SERIES_2_CONFIGS=("sf_25" "sf_50" "sf_100")
declare -a SERIES_3_CONFIGS=("streams_1" "streams_4" "streams_8" "streams_16")
declare -a SERIES_4_CONFIGS=("streams_1" "streams_4" "streams_8" "streams_16")
declare -a SERIES_5_CONFIGS=("max_nodes_sf" "max_nodes_streams")

# Timeouts (in seconds)
INFRA_TIMEOUT=3600       # 60 minutes for infrastructure (larger clusters)
BENCHMARK_TIMEOUT=14400  # 4 hours for benchmark run (SF100 + multinode)
DESTROY_TIMEOUT=900      # 15 minutes for cleanup

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# AWS Instance Pricing (eu-west-1, on-demand, USD/hour)
# https://aws.amazon.com/ec2/pricing/on-demand/
declare -A INSTANCE_PRICING=(
    ["m5d.large"]="0.113"
    ["r5d.large"]="0.144"
    ["r6id.xlarge"]="0.378"
    ["r6id.2xlarge"]="0.756"
    ["r6id.4xlarge"]="1.512"
)

# Estimated runtime per config (hours) - includes infra setup, data load, benchmark, cleanup
declare -A ESTIMATED_RUNTIME=(
    # Series 1: Node scaling - larger clusters take longer to set up
    ["s1_nodes_1"]="3"
    ["s1_nodes_4"]="4"
    ["s1_nodes_8"]="5"
    ["s1_nodes_16"]="6"
    # Series 2: SF scaling - larger data takes longer to load
    ["s2_sf_25"]="2"
    ["s2_sf_50"]="3"
    ["s2_sf_100"]="5"
    # Series 3: Cluster streams - 4-node clusters
    ["s3_streams_1"]="3"
    ["s3_streams_4"]="3"
    ["s3_streams_8"]="4"
    ["s3_streams_16"]="5"
    # Series 4: Single-node streams
    ["s4_streams_1"]="2"
    ["s4_streams_4"]="3"
    ["s4_streams_8"]="3"
    ["s4_streams_16"]="4"
    # Series 5: Stress tests - large clusters + data
    ["s5_max_nodes_sf"]="8"
    ["s5_max_nodes_streams"]="7"
)

# =============================================================================
# Global State
# =============================================================================

DRY_RUN=false
RESUME=false
NO_CLEANUP=false
SINGLE_EXPERIMENT=""
SINGLE_SERIES=""
PARALLEL_COUNT=1
CURRENT_EXPERIMENT=""
CLEANUP_NEEDED=false

# =============================================================================
# Utility Functions
# =============================================================================

log() {
    local level="$1"
    shift
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local color=""

    case "$level" in
        INFO)  color="$GREEN" ;;
        WARN)  color="$YELLOW" ;;
        ERROR) color="$RED" ;;
        DEBUG) color="$CYAN" ;;
        *)     color="$NC" ;;
    esac

    echo -e "${color}[${timestamp}] [${level}]${NC} $*"
    echo "[${timestamp}] [${level}] $*" >> "${LOG_DIR}/runner.log" 2>/dev/null || true
}

log_section() {
    local msg="$1"
    echo ""
    echo -e "${BLUE}${BOLD}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}${BOLD}  $msg${NC}"
    echo -e "${BLUE}${BOLD}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
}

die() {
    log ERROR "$1"
    exit 1
}

ensure_dir() {
    mkdir -p "$1" || die "Failed to create directory: $1"
}

# =============================================================================
# State Management
# =============================================================================

save_state() {
    local experiment="$1"
    local status="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    ensure_dir "$(dirname "${STATE_FILE}")"
    echo "${experiment}|${status}|${timestamp}" >> "${STATE_FILE}"
}

get_experiment_status() {
    local experiment="$1"
    if [[ -f "${STATE_FILE}" ]]; then
        grep "^${experiment}|" "${STATE_FILE}" | tail -1 | cut -d'|' -f2
    fi
}

is_experiment_completed() {
    local experiment="$1"
    local status=$(get_experiment_status "$experiment")
    [[ "$status" == "completed" ]]
}

reset_state() {
    log INFO "Resetting experiment state..."
    rm -f "${STATE_FILE}"
}

# =============================================================================
# Experiment Information
# =============================================================================

get_series_configs() {
    local series="$1"
    case "$series" in
        1) echo "${SERIES_1_CONFIGS[@]}" ;;
        2) echo "${SERIES_2_CONFIGS[@]}" ;;
        3) echo "${SERIES_3_CONFIGS[@]}" ;;
        4) echo "${SERIES_4_CONFIGS[@]}" ;;
        5) echo "${SERIES_5_CONFIGS[@]}" ;;
    esac
}

get_config_path() {
    local series="$1"
    local config="$2"
    echo "${CONFIG_DIR}/${SERIES_DIRS[$series]}/${config}.yaml"
}

get_experiment_id() {
    local series="$1"
    local config="$2"
    echo "s${series}_${config}"
}

count_total_experiments() {
    local total=0
    for series in 1 2 3 4 5; do
        local configs=($(get_series_configs $series))
        total=$((total + ${#configs[@]}))
    done
    echo $total
}

# =============================================================================
# Dry Run / Status Display
# =============================================================================

show_experiment_plan() {
    log_section "Extended Scalability Experiment Plan"

    local total_experiments=0
    local completed_experiments=0
    local pending_experiments=0

    for series in 1 2 3 4 5; do
        local series_name="${SERIES_NAMES[$series]}"
        local series_dir="${SERIES_DIRS[$series]}"
        local num_systems="${SERIES_SYSTEMS[$series]}"
        local configs=($(get_series_configs $series))
        local num_configs=${#configs[@]}

        echo -e "${MAGENTA}${BOLD}Series ${series}: ${series_name}${NC} (${num_systems} systems, ${num_configs} configs)"
        echo -e "${CYAN}─────────────────────────────────────────────────────────────${NC}"

        for config in "${configs[@]}"; do
            local experiment_id=$(get_experiment_id $series $config)
            local config_path=$(get_config_path $series $config)
            local status=$(get_experiment_status "$experiment_id")
            local status_icon=""
            local status_color=""

            case "$status" in
                completed)
                    status_icon="[DONE]"
                    status_color="$GREEN"
                    ((completed_experiments++))
                    ;;
                started|running)
                    status_icon="[RUNNING]"
                    status_color="$YELLOW"
                    ((pending_experiments++))
                    ;;
                failed|*_failed)
                    status_icon="[FAILED]"
                    status_color="$RED"
                    ((pending_experiments++))
                    ;;
                interrupted)
                    status_icon="[INTERRUPTED]"
                    status_color="$YELLOW"
                    ((pending_experiments++))
                    ;;
                *)
                    status_icon="[PENDING]"
                    status_color="$CYAN"
                    ((pending_experiments++))
                    ;;
            esac

            ((total_experiments++))

            # Extract key info from config
            local description=""
            case "$series" in
                1) description="${num_systems} systems × ${config#nodes_} nodes × SF50 × 4 streams" ;;
                2) description="${num_systems} systems × 1 node × SF${config#sf_} × 4 streams" ;;
                3) description="${num_systems} systems × 4 nodes × SF50 × ${config#streams_} streams" ;;
                4) description="${num_systems} systems × 1 node × SF50 × ${config#streams_} streams" ;;
                5)
                    if [[ "$config" == "max_nodes_sf" ]]; then
                        description="${num_systems} systems × 16 nodes × SF100 × 4 streams"
                    else
                        description="${num_systems} systems × 16 nodes × SF50 × 16 streams"
                    fi
                    ;;
            esac

            printf "  ${status_color}%-12s${NC} %-20s → %s\n" "$status_icon" "${config}.yaml" "$description"
        done
        echo ""
    done

    # Calculate total cost estimate
    local grand_total_cost=0
    local grand_total_hours=0
    local grand_max_instances=0

    for series in 1 2 3 4 5; do
        local configs=($(get_series_configs $series))
        local series_max_instances=0

        for config in "${configs[@]}"; do
            local experiment_id=$(get_experiment_id $series $config)
            local instance_info=$(get_experiment_instances $series $config)
            local instance_count=$(echo "$instance_info" | cut -d' ' -f2)
            local total_cost=$(get_experiment_total_cost $series $config)
            local runtime="${ESTIMATED_RUNTIME[$experiment_id]}"

            grand_total_cost=$(echo "scale=2; $grand_total_cost + $total_cost" | bc)
            grand_total_hours=$((grand_total_hours + runtime))
            if [[ $instance_count -gt $series_max_instances ]]; then
                series_max_instances=$instance_count
            fi
        done

        if [[ $series_max_instances -gt $grand_max_instances ]]; then
            grand_max_instances=$series_max_instances
        fi
    done

    # Summary
    echo -e "${BOLD}Summary${NC}"
    echo "─────────────────────────────────────────────────────────────"
    echo "  Total configs: $(count_total_experiments)"
    echo "  Total experiments: ${total_experiments}"
    echo "  Completed: ${completed_experiments}"
    echo "  Pending: ${pending_experiments}"
    echo ""

    # Cost summary
    echo -e "${BOLD}Cost Estimate${NC}"
    echo "─────────────────────────────────────────────────────────────"
    echo "  Max concurrent instances: ${grand_max_instances}"
    echo "  Total estimated runtime:  ~${grand_total_hours}h"
    echo -e "  Total estimated cost:     ${GREEN}\$$(printf '%.2f' $grand_total_cost)${NC} (on-demand pricing)"
    echo ""
    echo "  Per-series breakdown:"
    for series in 1 2 3 4 5; do
        local configs=($(get_series_configs $series))
        local series_cost=0
        for config in "${configs[@]}"; do
            local cost=$(get_experiment_total_cost $series $config)
            series_cost=$(echo "scale=2; $series_cost + $cost" | bc)
        done
        printf "    Series %d: %-30s \$%7.2f\n" "$series" "${SERIES_NAMES[$series]}" "$series_cost"
    done
    echo ""

    # Instance count warning
    echo -e "${YELLOW}${BOLD}Infrastructure Requirements:${NC}"
    echo "  Series 1 (16 nodes): Up to 64 instances (4 systems × 16 nodes)"
    echo "  Series 5 (stress):   Up to 64 instances (4 systems × 16 nodes)"
    echo ""
    echo "  Verify AWS quotas: aws service-quotas get-service-quota \\"
    echo "    --service-code ec2 --quota-code L-1216C47A"
    echo ""
}

get_experiment_description() {
    local series="$1"
    local config="$2"
    local num_systems="${SERIES_SYSTEMS[$series]}"

    case "$series" in
        1)
            local nodes="${config#nodes_}"
            case "$nodes" in
                1)  echo "Single-node baseline | ${num_systems} DBs, SF50, 4 streams, r6id.2xlarge (64GB)" ;;
                4)  echo "4-node cluster | ${num_systems} DBs, SF50, 4 streams, r5d.large×4 (64GB)" ;;
                8)  echo "8-node cluster | ${num_systems} DBs, SF50, 4 streams, m5d.large×8 (64GB)" ;;
                16) echo "16-node cluster | ${num_systems} DBs, SF50, 4 streams, m5d.large×16 (128GB)" ;;
            esac
            ;;
        2)
            local sf="${config#sf_}"
            local instance=""
            case "$sf" in
                25)  instance="r6id.xlarge (32GB)" ;;
                50)  instance="r6id.2xlarge (64GB)" ;;
                100) instance="r6id.4xlarge (128GB)" ;;
            esac
            echo "Data scaling SF${sf} | ${num_systems} DBs, 1 node, 4 streams, ${instance}"
            ;;
        3)
            local streams="${config#streams_}"
            local instance=""
            local stream_word="streams"
            [[ "$streams" == "1" ]] && stream_word="stream"
            case "$streams" in
                1)  instance="r5d.large×4 (64GB)" ;;
                4)  instance="r6id.xlarge×4 (128GB)" ;;
                8)  instance="r6id.2xlarge×4 (256GB)" ;;
                16) instance="r6id.4xlarge×4 (512GB)" ;;
            esac
            echo "Cluster concurrency ${streams} ${stream_word} | ${num_systems} DBs, 4 nodes, SF50, ${instance}"
            ;;
        4)
            local streams="${config#streams_}"
            local instance=""
            local stream_word="streams"
            [[ "$streams" == "1" ]] && stream_word="stream"
            case "$streams" in
                1|4) instance="r6id.xlarge (32GB)" ;;
                8)   instance="r6id.2xlarge (64GB)" ;;
                16)  instance="r6id.4xlarge (128GB)" ;;
            esac
            echo "Single-node concurrency ${streams} ${stream_word} | ${num_systems} DBs, SF50, ${instance}"
            ;;
        5)
            if [[ "$config" == "max_nodes_sf" ]]; then
                echo "STRESS: Max data + nodes | ${num_systems} DBs, 16 nodes, SF100, 4 streams, r6id.xlarge×16 (512GB)"
            else
                echo "STRESS: Max concurrency + nodes | ${num_systems} DBs, 16 nodes, SF100, 16 streams, r6id.xlarge×16 (512GB)"
            fi
            ;;
    esac
}

# Get instance details for an experiment: "instance_type count"
get_experiment_instances() {
    local series="$1"
    local config="$2"
    local num_systems="${SERIES_SYSTEMS[$series]}"

    case "$series" in
        1)
            local nodes="${config#nodes_}"
            case "$nodes" in
                1)  echo "r6id.2xlarge $((num_systems * 1))" ;;
                4)  echo "r5d.large $((num_systems * nodes))" ;;
                8)  echo "m5d.large $((num_systems * nodes))" ;;
                16) echo "m5d.large $((num_systems * nodes))" ;;
            esac
            ;;
        2)
            local sf="${config#sf_}"
            case "$sf" in
                25)  echo "r6id.xlarge $num_systems" ;;
                50)  echo "r6id.2xlarge $num_systems" ;;
                100) echo "r6id.4xlarge $num_systems" ;;
            esac
            ;;
        3)
            local streams="${config#streams_}"
            local nodes=4
            case "$streams" in
                1)  echo "r5d.large $((num_systems * nodes))" ;;
                4)  echo "r6id.xlarge $((num_systems * nodes))" ;;
                8)  echo "r6id.2xlarge $((num_systems * nodes))" ;;
                16) echo "r6id.4xlarge $((num_systems * nodes))" ;;
            esac
            ;;
        4)
            local streams="${config#streams_}"
            case "$streams" in
                1|4) echo "r6id.xlarge $num_systems" ;;
                8)   echo "r6id.2xlarge $num_systems" ;;
                16)  echo "r6id.4xlarge $num_systems" ;;
            esac
            ;;
        5)
            local nodes=16
            echo "r6id.xlarge $((num_systems * nodes))"
            ;;
    esac
}

# Calculate cost per hour for an experiment
get_experiment_cost_per_hour() {
    local series="$1"
    local config="$2"
    local instance_info=$(get_experiment_instances $series $config)
    local instance_type=$(echo "$instance_info" | cut -d' ' -f1)
    local count=$(echo "$instance_info" | cut -d' ' -f2)
    local price_per_hour="${INSTANCE_PRICING[$instance_type]}"

    echo "scale=2; $count * $price_per_hour" | bc
}

# Calculate total estimated cost for an experiment
get_experiment_total_cost() {
    local series="$1"
    local config="$2"
    local experiment_id=$(get_experiment_id $series $config)
    local cost_per_hour=$(get_experiment_cost_per_hour $series $config)
    local runtime="${ESTIMATED_RUNTIME[$experiment_id]}"

    echo "scale=2; $cost_per_hour * $runtime" | bc
}

list_experiments() {
    echo ""
    echo -e "${BOLD}Extended Scalability Experiments Status${NC}"
    echo "========================================"

    local grand_total_cost=0
    local grand_total_hours=0
    local grand_max_instances=0
    local enabled_total_cost=0
    local enabled_total_hours=0

    for series in 1 2 3 4 5; do
        local is_enabled="${SERIES_ENABLED[$series]}"
        local enabled_marker=""
        local series_color="$MAGENTA"
        if [[ "$is_enabled" == "1" ]]; then
            enabled_marker="${GREEN}[ENABLED]${NC} "
        else
            enabled_marker="${YELLOW}[DISABLED]${NC} "
            series_color="$YELLOW"
        fi

        echo ""
        echo -e "${series_color}${BOLD}Series ${series}: ${SERIES_NAMES[$series]}${NC} ${enabled_marker}"
        echo -e "${CYAN}────────────────────────────────────────────────────────────────────────────────────────────────────────────${NC}"

        local configs=($(get_series_configs $series))
        local series_total_cost=0
        local series_total_hours=0
        local series_max_instances=0

        for config in "${configs[@]}"; do
            local experiment_id=$(get_experiment_id $series $config)
            local config_path=$(get_config_path $series $config)
            local status=$(get_experiment_status "$experiment_id")
            local description=$(get_experiment_description $series $config)
            local status_icon=""
            local status_color=""

            # Get instance and cost info
            local instance_info=$(get_experiment_instances $series $config)
            local instance_type=$(echo "$instance_info" | cut -d' ' -f1)
            local instance_count=$(echo "$instance_info" | cut -d' ' -f2)
            local cost_per_hour=$(get_experiment_cost_per_hour $series $config)
            local runtime="${ESTIMATED_RUNTIME[$experiment_id]}"
            local total_cost=$(get_experiment_total_cost $series $config)

            # Track series totals
            series_total_cost=$(echo "scale=2; $series_total_cost + $total_cost" | bc)
            series_total_hours=$((series_total_hours + runtime))
            if [[ $instance_count -gt $series_max_instances ]]; then
                series_max_instances=$instance_count
            fi

            [[ -z "$status" ]] && status="pending"

            case "$status" in
                completed)    status_icon="DONE"; status_color="$GREEN" ;;
                started)      status_icon="RUNNING"; status_color="$YELLOW" ;;
                *_failed)     status_icon="FAILED"; status_color="$RED" ;;
                interrupted)  status_icon="STOPPED"; status_color="$YELLOW" ;;
                *)            status_icon="PENDING"; status_color="$CYAN" ;;
            esac

            if [[ ! -f "$config_path" ]]; then
                status_icon="MISSING"
                status_color="$RED"
            fi

            # Format cost info
            local cost_info="${instance_count}× ${instance_type} | \$${cost_per_hour}/hr × ${runtime}h = \$${total_cost}"

            printf "  ${status_color}%-8s${NC} %-20s %s\n" "[$status_icon]" "$experiment_id" "$description"
            printf "           ${YELLOW}%-21s %s${NC}\n" "" "$cost_info"
        done

        # Series summary
        echo -e "  ${CYAN}─────────────────────────────────────────────────────────────────────────────────────────────────────────${NC}"
        printf "  ${BOLD}Series %d Total:${NC} Max %d instances concurrent | ~%dh runtime | ${GREEN}\$%.2f estimated cost${NC}\n" \
            "$series" "$series_max_instances" "$series_total_hours" "$series_total_cost"

        # Update grand totals
        grand_total_cost=$(echo "scale=2; $grand_total_cost + $series_total_cost" | bc)
        grand_total_hours=$((grand_total_hours + series_total_hours))
        if [[ $series_max_instances -gt $grand_max_instances ]]; then
            grand_max_instances=$series_max_instances
        fi

        # Track enabled totals separately
        if [[ "$is_enabled" == "1" ]]; then
            enabled_total_cost=$(echo "scale=2; $enabled_total_cost + $series_total_cost" | bc)
            enabled_total_hours=$((enabled_total_hours + series_total_hours))
        fi
    done

    # Grand total
    echo ""
    echo -e "${BLUE}════════════════════════════════════════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}ENABLED SERIES: ${NC}~${enabled_total_hours}h runtime | ${GREEN}${BOLD}\$$(printf '%.2f' $enabled_total_cost) estimated cost${NC}"
    echo -e "${BOLD}ALL SERIES:     ${NC}Max ${grand_max_instances} instances concurrent | ~${grand_total_hours}h runtime | ${GREEN}\$$(printf '%.2f' $grand_total_cost) estimated cost${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════════════════════════════════════════════════════${NC}"

    echo ""
    echo -e "${BOLD}Legend:${NC}"
    echo "  DBs = Database systems tested (Exasol, ClickHouse, Trino, StarRocks, DuckDB)"
    echo "  SF  = TPC-H Scale Factor in GB"
    echo ""
    echo -e "${BOLD}Instance Pricing (eu-west-1, on-demand):${NC}"
    echo "  m5d.large    = \$0.113/hr (2 vCPU, 8GB RAM, NVMe SSD)"
    echo "  r5d.large    = \$0.144/hr (2 vCPU, 16GB RAM, NVMe SSD)"
    echo "  r6id.xlarge  = \$0.378/hr (4 vCPU, 32GB RAM, NVMe SSD)"
    echo "  r6id.2xlarge = \$0.756/hr (8 vCPU, 64GB RAM, NVMe SSD)"
    echo "  r6id.4xlarge = \$1.512/hr (16 vCPU, 128GB RAM, NVMe SSD)"
    echo ""
    echo -e "${YELLOW}Note: Costs are estimates. Actual costs depend on runtime, data transfer, and EBS storage.${NC}"
    echo ""
}

# =============================================================================
# Infrastructure Management
# =============================================================================

destroy_infrastructure() {
    local config="$1"
    local experiment="$2"
    local log_file="${LOG_DIR}/${experiment}_destroy.log"

    log INFO "Destroying infrastructure for ${experiment}..."

    if $DRY_RUN; then
        log INFO "[DRY-RUN] Would destroy infrastructure"
        return 0
    fi

    timeout "${DESTROY_TIMEOUT}" python -m benchkit infra destroy -c "$config" \
        >> "$log_file" 2>&1
    local exit_code=$?

    if [[ $exit_code -eq 0 ]]; then
        log INFO "Infrastructure destroyed successfully"
        return 0
    elif [[ $exit_code -eq 124 ]]; then
        log WARN "Infrastructure destroy timed out after ${DESTROY_TIMEOUT}s"
        return 1
    else
        log WARN "Infrastructure destroy failed (exit code: $exit_code)"
        return 1
    fi
}

force_cleanup() {
    local config="$1"
    local experiment="$2"

    log WARN "Attempting force cleanup for ${experiment}..."

    for attempt in 1 2 3; do
        log INFO "Cleanup attempt ${attempt}/3..."
        if destroy_infrastructure "$config" "$experiment"; then
            return 0
        fi
        sleep 10
    done

    log ERROR "Force cleanup failed after 3 attempts. Manual intervention may be required."
    return 1
}

# =============================================================================
# Experiment Execution
# =============================================================================

validate_config() {
    local config="$1"
    local experiment="$2"

    log INFO "Validating config: ${config}"

    if [[ ! -f "$config" ]]; then
        log ERROR "Config file not found: ${config}"
        return 1
    fi

    # Check required fields
    for field in project_id systems workload env; do
        if ! grep -q "^${field}:" "$config"; then
            log ERROR "Missing required field '${field}' in ${config}"
            return 1
        fi
    done

    # Run benchkit check
    if ! python -m benchkit check -c "$config" > /dev/null 2>&1; then
        log WARN "Config validation warning for ${experiment}"
    fi

    log INFO "Config validation passed"
    return 0
}

run_experiment() {
    local series="$1"
    local config_name="$2"
    local experiment_id=$(get_experiment_id $series $config_name)
    local config=$(get_config_path $series $config_name)
    local log_file="${LOG_DIR}/${experiment_id}.log"
    local start_time=$(date +%s)

    log_section "Running Experiment: ${experiment_id}"
    log INFO "Series: ${SERIES_NAMES[$series]}"
    log INFO "Config: ${config}"

    # Check if already completed (resume mode)
    if $RESUME && is_experiment_completed "$experiment_id"; then
        log INFO "Experiment ${experiment_id} already completed, skipping..."
        return 0
    fi

    # Validate config
    if ! validate_config "$config" "$experiment_id"; then
        save_state "$experiment_id" "config_error"
        return 1
    fi

    if $DRY_RUN; then
        log INFO "[DRY-RUN] Would run experiment: ${experiment_id}"
        return 0
    fi

    # Mark as started
    save_state "$experiment_id" "started"
    CURRENT_EXPERIMENT="$experiment_id"
    CLEANUP_NEEDED=true

    # Create log file
    ensure_dir "$(dirname "$log_file")"
    echo "=== Experiment: ${experiment_id} ===" > "$log_file"
    echo "Started: $(date)" >> "$log_file"
    echo "" >> "$log_file"

    # Step 1: Provision infrastructure
    log INFO "Step 1/3: Provisioning infrastructure..."
    echo "=== Infrastructure Provisioning ===" >> "$log_file"

    timeout "${INFRA_TIMEOUT}" python -m benchkit infra apply -c "$config" \
        >> "$log_file" 2>&1
    local infra_exit=$?

    if [[ $infra_exit -ne 0 ]]; then
        if [[ $infra_exit -eq 124 ]]; then
            log ERROR "Infrastructure provisioning timed out after ${INFRA_TIMEOUT}s"
            save_state "$experiment_id" "infra_timeout"
        else
            log ERROR "Infrastructure provisioning failed (exit code: $infra_exit)"
            save_state "$experiment_id" "infra_failed"
        fi
        cleanup_experiment "$config" "$experiment_id"
        return 1
    fi
    log INFO "Infrastructure provisioned successfully"

    # Step 2: Run full benchmark
    log INFO "Step 2/3: Running benchmark (setup + load + run)..."
    echo "" >> "$log_file"
    echo "=== Benchmark Execution ===" >> "$log_file"

    timeout "${BENCHMARK_TIMEOUT}" python -m benchkit run --full -c "$config" \
        >> "$log_file" 2>&1
    local bench_exit=$?

    if [[ $bench_exit -ne 0 ]]; then
        if [[ $bench_exit -eq 124 ]]; then
            log ERROR "Benchmark timed out after ${BENCHMARK_TIMEOUT}s"
            save_state "$experiment_id" "benchmark_timeout"
        else
            log ERROR "Benchmark failed (exit code: $bench_exit)"
            save_state "$experiment_id" "benchmark_failed"
        fi
        cleanup_experiment "$config" "$experiment_id"
        return 1
    fi
    log INFO "Benchmark completed successfully"

    # Step 3: Cleanup infrastructure
    log INFO "Step 3/3: Cleaning up infrastructure..."
    cleanup_experiment "$config" "$experiment_id"

    # Calculate duration
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    local duration_min=$((duration / 60))

    log INFO "Experiment ${experiment_id} completed in ${duration_min} minutes"
    save_state "$experiment_id" "completed"
    CLEANUP_NEEDED=false

    return 0
}

cleanup_experiment() {
    local config="$1"
    local experiment="$2"

    if $NO_CLEANUP; then
        log WARN "Skipping cleanup (--no-cleanup flag set)"
        return 0
    fi

    if ! destroy_infrastructure "$config" "$experiment"; then
        force_cleanup "$config" "$experiment"
    fi

    CLEANUP_NEEDED=false
}

run_series() {
    local series="$1"
    local configs=($(get_series_configs $series))
    local num_configs=${#configs[@]}
    local completed=0
    local failed=0

    log_section "Series ${series}: ${SERIES_NAMES[$series]}"
    log INFO "Configs to run: ${configs[*]}"
    log INFO "Total: ${num_configs} experiments"

    for i in "${!configs[@]}"; do
        local config="${configs[$i]}"
        local num=$((i + 1))

        log INFO "Progress: ${num}/${num_configs} - Starting ${config}"

        if run_experiment "$series" "$config"; then
            ((completed++))
        else
            ((failed++))
        fi

        # Brief pause between experiments
        if [[ $num -lt $num_configs ]] && ! $DRY_RUN; then
            log INFO "Waiting 30 seconds before next experiment..."
            sleep 30
        fi
    done

    log INFO "Series ${series} complete: ${completed} succeeded, ${failed} failed"
    return $([[ $failed -eq 0 ]] && echo 0 || echo 1)
}

# =============================================================================
# Signal Handling
# =============================================================================

cleanup_on_exit() {
    local exit_code=$?

    echo ""
    log WARN "Received interrupt signal..."

    if $CLEANUP_NEEDED && [[ -n "$CURRENT_EXPERIMENT" ]]; then
        log WARN "Cleaning up running experiment: ${CURRENT_EXPERIMENT}"

        # Find config for current experiment
        for series in 1 2 3 4 5; do
            local configs=($(get_series_configs $series))
            for config in "${configs[@]}"; do
                local exp_id=$(get_experiment_id $series $config)
                if [[ "$exp_id" == "$CURRENT_EXPERIMENT" ]]; then
                    local config_path=$(get_config_path $series $config)
                    save_state "$CURRENT_EXPERIMENT" "interrupted"
                    if ! $DRY_RUN; then
                        force_cleanup "$config_path" "$CURRENT_EXPERIMENT"
                    fi
                    break 2
                fi
            done
        done
    fi

    log INFO "Experiment runner terminated"
    exit $exit_code
}

trap cleanup_on_exit SIGINT SIGTERM

# =============================================================================
# Results Aggregation
# =============================================================================

aggregate_results() {
    log_section "Aggregating Results"

    local summary_file="${LOG_DIR}/experiment_summary.md"

    cat > "$summary_file" << 'EOF'
# Extended Scalability Experiment Results Summary

## Series Overview

| Series | Name | Configs | Status |
|--------|------|---------|--------|
EOF

    for series in 1 2 3 4 5; do
        local configs=($(get_series_configs $series))
        local total=${#configs[@]}
        local completed=0
        local failed=0

        for config in "${configs[@]}"; do
            local exp_id=$(get_experiment_id $series $config)
            local status=$(get_experiment_status "$exp_id")
            case "$status" in
                completed) ((completed++)) ;;
                *_failed|failed) ((failed++)) ;;
            esac
        done

        local status_text="${completed}/${total} completed"
        [[ $failed -gt 0 ]] && status_text="${status_text}, ${failed} failed"

        echo "| ${series} | ${SERIES_NAMES[$series]} | ${total} | ${status_text} |" >> "$summary_file"
    done

    echo "" >> "$summary_file"
    echo "## Detailed Results" >> "$summary_file"
    echo "" >> "$summary_file"

    for series in 1 2 3 4 5; do
        echo "### Series ${series}: ${SERIES_NAMES[$series]}" >> "$summary_file"
        echo "" >> "$summary_file"
        echo "| Experiment | Status | Duration |" >> "$summary_file"
        echo "|------------|--------|----------|" >> "$summary_file"

        local configs=($(get_series_configs $series))
        for config in "${configs[@]}"; do
            local exp_id=$(get_experiment_id $series $config)
            local status=$(get_experiment_status "$exp_id")
            [[ -z "$status" ]] && status="pending"
            echo "| ${exp_id} | ${status} | - |" >> "$summary_file"
        done
        echo "" >> "$summary_file"
    done

    echo "Generated: $(date)" >> "$summary_file"

    log INFO "Results summary saved to: ${summary_file}"
    cat "$summary_file"
}

# =============================================================================
# Main
# =============================================================================

show_help() {
    cat << 'EOF'
Extended Scalability Experiment Runner
======================================

Orchestrates comprehensive scalability benchmark experiments across
5 database systems (Exasol, ClickHouse, Trino, StarRocks, DuckDB)
and 3 scaling dimensions (Nodes, Scale Factor, Streams).

Usage:
  ./configs/extended_scalability/run_all.sh [OPTIONS]

Options:
  --dry-run         Show experiment plan without executing
  --list            List all experiments and their status
  --series N        Run only series N (1-5), ignores enabled/disabled status
  --enable N        Enable series N (can be repeated, e.g., --enable 3 --enable 5)
  --disable N       Disable series N (can be repeated)
  --all             Enable all series (overrides defaults)
  --resume          Skip already completed experiments
  --experiment X    Run single experiment by ID (e.g., s1_nodes_4)
  --no-cleanup      Don't destroy infrastructure after each run
  --parallel N      Run N experiments concurrently (default: 1)
  --reset           Reset experiment state
  --help            Show this help message

Series:                                                          Default:
  1. Node Scaling      - 4 configs (1/4/8/16 nodes), 4 systems   [ENABLED]
  2. SF Scaling        - 3 configs (SF 25/50/100), 5 systems     [ENABLED]
  3. Streams (Cluster) - 4 configs (1/4/8/16 streams), 4 systems [DISABLED]
  4. Streams (Single)  - 4 configs (1/4/8/16 streams), 5 systems [ENABLED]
  5. Stress Tests      - 2 configs (max nodes+SF, max nodes+streams) [DISABLED]

Examples:
  # View experiment plan (dry-run)
  ./configs/extended_scalability/run_all.sh --dry-run

  # View current status
  ./configs/extended_scalability/run_all.sh --list

  # Run all enabled series (1, 2, 4 by default)
  ./configs/extended_scalability/run_all.sh

  # Run specific series (ignores enabled/disabled)
  ./configs/extended_scalability/run_all.sh --series 1

  # Enable additional series for this run
  ./configs/extended_scalability/run_all.sh --enable 3 --enable 5

  # Run all series (enable everything)
  ./configs/extended_scalability/run_all.sh --all

  # Resume after interruption
  ./configs/extended_scalability/run_all.sh --resume

  # Run single experiment
  ./configs/extended_scalability/run_all.sh --experiment s1_nodes_4

  # Debug: run without cleanup
  ./configs/extended_scalability/run_all.sh --experiment s1_nodes_1 --no-cleanup

EOF
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --resume)
                RESUME=true
                shift
                ;;
            --no-cleanup)
                NO_CLEANUP=true
                shift
                ;;
            --series)
                SINGLE_SERIES="$2"
                if [[ ! "$SINGLE_SERIES" =~ ^[1-5]$ ]]; then
                    die "Invalid series: $SINGLE_SERIES. Must be 1-5."
                fi
                shift 2
                ;;
            --enable)
                if [[ ! "$2" =~ ^[1-5]$ ]]; then
                    die "Invalid series: $2. Must be 1-5."
                fi
                SERIES_ENABLED[$2]="1"
                shift 2
                ;;
            --disable)
                if [[ ! "$2" =~ ^[1-5]$ ]]; then
                    die "Invalid series: $2. Must be 1-5."
                fi
                SERIES_ENABLED[$2]="0"
                shift 2
                ;;
            --all)
                for s in 1 2 3 4 5; do
                    SERIES_ENABLED[$s]="1"
                done
                shift
                ;;
            --experiment)
                SINGLE_EXPERIMENT="$2"
                shift 2
                ;;
            --parallel)
                PARALLEL_COUNT="$2"
                shift 2
                ;;
            --reset)
                reset_state
                exit 0
                ;;
            --list)
                list_experiments
                exit 0
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                die "Unknown option: $1. Use --help for usage."
                ;;
        esac
    done
}

main() {
    parse_args "$@"

    # Setup logging
    ensure_dir "$LOG_DIR"

    log_section "Extended Scalability Experiment Runner"
    log INFO "Repository root: ${REPO_ROOT}"
    log INFO "Config directory: ${CONFIG_DIR}"
    log INFO "Results directory: ${RESULTS_DIR}"
    log INFO "Log directory: ${LOG_DIR}"
    log INFO "Dry run: ${DRY_RUN}"
    log INFO "Resume mode: ${RESUME}"
    log INFO "No cleanup: ${NO_CLEANUP}"

    # Verify we're in the right directory
    if [[ ! -f "${REPO_ROOT}/pyproject.toml" ]]; then
        die "Script must be run from the benchkit repository"
    fi

    # Show plan in dry-run mode
    if $DRY_RUN && [[ -z "$SINGLE_EXPERIMENT" ]] && [[ -z "$SINGLE_SERIES" ]]; then
        show_experiment_plan
        exit 0
    fi

    # Handle single experiment
    if [[ -n "$SINGLE_EXPERIMENT" ]]; then
        # Parse experiment ID (e.g., s1_nodes_4)
        if [[ "$SINGLE_EXPERIMENT" =~ ^s([1-5])_(.+)$ ]]; then
            local series="${BASH_REMATCH[1]}"
            local config="${BASH_REMATCH[2]}"

            # Verify config exists
            local config_path=$(get_config_path $series $config)
            if [[ ! -f "$config_path" ]]; then
                die "Config not found: ${config_path}"
            fi

            run_experiment "$series" "$config"
            exit $?
        else
            die "Invalid experiment ID format: ${SINGLE_EXPERIMENT}. Use format: s<N>_<config> (e.g., s1_nodes_4)"
        fi
    fi

    # Determine which series to run
    local series_to_run=()
    if [[ -n "$SINGLE_SERIES" ]]; then
        # --series flag overrides enabled/disabled status
        series_to_run=($SINGLE_SERIES)
        log INFO "Running specific series: ${SINGLE_SERIES} (ignoring enabled/disabled status)"
    else
        # Only run enabled series
        for s in 1 2 3 4 5; do
            if [[ "${SERIES_ENABLED[$s]}" == "1" ]]; then
                series_to_run+=($s)
            fi
        done
        if [[ ${#series_to_run[@]} -eq 0 ]]; then
            log WARN "No series enabled. Use --enable N or --all to enable series."
            exit 0
        fi
    fi

    log INFO "Series to run: ${series_to_run[*]}"

    # Show disabled series
    local disabled_series=()
    for s in 1 2 3 4 5; do
        if [[ "${SERIES_ENABLED[$s]}" == "0" ]]; then
            disabled_series+=($s)
        fi
    done
    if [[ ${#disabled_series[@]} -gt 0 ]] && [[ -z "$SINGLE_SERIES" ]]; then
        log INFO "Disabled series (use --enable N to include): ${disabled_series[*]}"
    fi

    # Run series
    local total_completed=0
    local total_failed=0

    for series in "${series_to_run[@]}"; do
        if run_series "$series"; then
            ((total_completed++))
        else
            ((total_failed++))
        fi

        # Pause between series
        if [[ $series -lt ${series_to_run[-1]} ]] && ! $DRY_RUN; then
            log INFO "Waiting 60 seconds before next series..."
            sleep 60
        fi
    done

    # Aggregate results
    if ! $DRY_RUN; then
        aggregate_results
    fi

    # Final summary
    log_section "Experiment Run Complete"
    log INFO "Series completed: ${total_completed}"
    log INFO "Series with failures: ${total_failed}"

    if [[ $total_failed -gt 0 ]]; then
        log WARN "Some experiments failed. Check logs in ${LOG_DIR}/"
        exit 1
    fi

    log INFO "All experiments completed successfully!"
    exit 0
}

main "$@"
