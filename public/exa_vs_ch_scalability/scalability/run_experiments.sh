#!/usr/bin/env bash
#
# Scalability Experiment Runner
# =============================
# Runs all scalability benchmark experiments with proper resource cleanup.
#
# Features:
# - Runs experiments in priority order
# - Automatic infrastructure cleanup after each experiment
# - Resume capability (skips completed experiments)
# - Comprehensive logging
# - Signal handling for graceful shutdown
# - Timeout protection
# - Dry-run mode for validation
#
# Usage:
#   ./configs/scalability/run_experiments.sh [OPTIONS]
#
# Options:
#   --dry-run       Validate configs without running
#   --resume        Skip already completed experiments
#   --experiment X  Run only experiment X (e.g., mvr_32)
#   --force         Force re-run even if results exist
#   --no-cleanup    Don't destroy infrastructure after each run
#   --help          Show this help message
#

set -o pipefail

# =============================================================================
# Configuration
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
CONFIG_DIR="${REPO_ROOT}/configs/scalability"
RESULTS_DIR="${REPO_ROOT}/results"
LOG_DIR="${REPO_ROOT}/logs/scalability"
STATE_FILE="${LOG_DIR}/.experiment_state"

# Experiment priority order
EXPERIMENTS=(
    "mvr_32"      # Priority 1: Shows ClickHouse failure threshold
    "conc_10"     # Priority 2: Start of concurrency cliff
    "mvr_16"      # Priority 3: Extreme constraint demonstration
    "conc_15"     # Priority 4: Concurrency cliff progression
    "node_1"      # Priority 5: Single-node baseline
    "mvr_64"      # Priority 6: Find ClickHouse success threshold
    "conc_20"     # Priority 7: High concurrency stress test
    "node_2"      # Priority 8: 2-node scaling
    "node_4"      # Priority 9: 4-node scaling
)

# Timeouts (in seconds)
INFRA_TIMEOUT=1800      # 30 minutes for infrastructure
BENCHMARK_TIMEOUT=7200  # 2 hours for benchmark run
DESTROY_TIMEOUT=600     # 10 minutes for cleanup

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# =============================================================================
# Global State
# =============================================================================

DRY_RUN=false
RESUME=false
FORCE=false
NO_CLEANUP=false
SINGLE_EXPERIMENT=""
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
    echo "[${timestamp}] [${level}] $*" >> "${LOG_DIR}/runner.log"
}

log_section() {
    local msg="$1"
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $msg${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
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
# Infrastructure Management
# =============================================================================

check_infrastructure_exists() {
    local config="$1"
    local project_id=$(grep "^project_id:" "$config" | awk '{print $2}' | tr -d '"')
    local tf_dir="${RESULTS_DIR}/${project_id}/terraform"

    if [[ -d "$tf_dir" ]] && [[ -f "${tf_dir}/terraform.tfstate" ]]; then
        # Check if there are actual resources
        if grep -q '"type":' "${tf_dir}/terraform.tfstate" 2>/dev/null; then
            return 0
        fi
    fi
    return 1
}

destroy_infrastructure() {
    local config="$1"
    local experiment="$2"
    local log_file="${LOG_DIR}/${experiment}_destroy.log"

    log INFO "Destroying infrastructure for ${experiment}..."

    if $DRY_RUN; then
        log INFO "[DRY-RUN] Would destroy infrastructure"
        return 0
    fi

    # Run destroy with timeout
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

    # Try destroy up to 3 times
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
    local experiment="$1"
    local config="${CONFIG_DIR}/${experiment}.yaml"
    local log_file="${LOG_DIR}/${experiment}.log"
    local start_time=$(date +%s)

    log_section "Running Experiment: ${experiment}"

    # Check if already completed (resume mode)
    if $RESUME && is_experiment_completed "$experiment"; then
        log INFO "Experiment ${experiment} already completed, skipping..."
        return 0
    fi

    # Validate config
    if ! validate_config "$config" "$experiment"; then
        save_state "$experiment" "config_error"
        return 1
    fi

    if $DRY_RUN; then
        log INFO "[DRY-RUN] Would run experiment: ${experiment}"
        log INFO "[DRY-RUN] Config: ${config}"
        return 0
    fi

    # Mark as started
    save_state "$experiment" "started"
    CURRENT_EXPERIMENT="$experiment"
    CLEANUP_NEEDED=true

    # Step 1: Provision infrastructure
    log INFO "Step 1/3: Provisioning infrastructure..."
    echo "=== Infrastructure Provisioning ===" >> "$log_file"

    timeout "${INFRA_TIMEOUT}" python -m benchkit infra apply -c "$config" \
        >> "$log_file" 2>&1
    local infra_exit=$?

    if [[ $infra_exit -ne 0 ]]; then
        log ERROR "Infrastructure provisioning failed (exit code: $infra_exit)"
        save_state "$experiment" "infra_failed"
        cleanup_experiment "$config" "$experiment"
        return 1
    fi
    log INFO "Infrastructure provisioned successfully"

    # Step 2: Run full benchmark (setup + load + run)
    log INFO "Step 2/3: Running benchmark (setup + load + run)..."
    echo "" >> "$log_file"
    echo "=== Benchmark Execution ===" >> "$log_file"

    timeout "${BENCHMARK_TIMEOUT}" python -m benchkit run --full -c "$config" \
        >> "$log_file" 2>&1
    local bench_exit=$?

    if [[ $bench_exit -ne 0 ]]; then
        if [[ $bench_exit -eq 124 ]]; then
            log ERROR "Benchmark timed out after ${BENCHMARK_TIMEOUT}s"
            save_state "$experiment" "timeout"
        else
            log ERROR "Benchmark failed (exit code: $bench_exit)"
            save_state "$experiment" "benchmark_failed"
        fi
        cleanup_experiment "$config" "$experiment"
        return 1
    fi
    log INFO "Benchmark completed successfully"

    # Step 3: Cleanup infrastructure
    log INFO "Step 3/3: Cleaning up infrastructure..."
    cleanup_experiment "$config" "$experiment"

    # Calculate duration
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    local duration_min=$((duration / 60))

    log INFO "Experiment ${experiment} completed in ${duration_min} minutes"
    save_state "$experiment" "completed"
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

# =============================================================================
# Signal Handling
# =============================================================================

cleanup_on_exit() {
    local exit_code=$?

    echo ""
    log WARN "Received interrupt signal..."

    if $CLEANUP_NEEDED && [[ -n "$CURRENT_EXPERIMENT" ]]; then
        log WARN "Cleaning up running experiment: ${CURRENT_EXPERIMENT}"
        local config="${CONFIG_DIR}/${CURRENT_EXPERIMENT}.yaml"

        save_state "$CURRENT_EXPERIMENT" "interrupted"

        if ! $DRY_RUN; then
            force_cleanup "$config" "$CURRENT_EXPERIMENT"
        fi
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
# Scalability Experiment Results Summary

| Experiment | Status | Duration | Notes |
|------------|--------|----------|-------|
EOF

    for experiment in "${EXPERIMENTS[@]}"; do
        local status=$(get_experiment_status "$experiment")
        local status_emoji=""

        case "$status" in
            completed)     status_emoji="✅" ;;
            started)       status_emoji="🔄" ;;
            interrupted)   status_emoji="⚠️" ;;
            *_failed)      status_emoji="❌" ;;
            config_error)  status_emoji="🚫" ;;
            "")            status_emoji="⏸️" ;;
            *)             status_emoji="❓" ;;
        esac

        echo "| ${experiment} | ${status_emoji} ${status:-pending} | - | |" >> "$summary_file"
    done

    echo "" >> "$summary_file"
    echo "Generated: $(date)" >> "$summary_file"

    log INFO "Results summary saved to: ${summary_file}"
    cat "$summary_file"
}

collect_benchmark_data() {
    log INFO "Collecting benchmark data from completed experiments..."

    local output_dir="${LOG_DIR}/collected_results"
    ensure_dir "$output_dir"

    for experiment in "${EXPERIMENTS[@]}"; do
        if is_experiment_completed "$experiment"; then
            local project_id="scalability_${experiment}"
            local results_path="${RESULTS_DIR}/${project_id}"

            if [[ -d "$results_path" ]]; then
                log INFO "Copying results for ${experiment}..."
                cp -r "$results_path" "${output_dir}/"
            fi
        fi
    done

    log INFO "Collected results saved to: ${output_dir}"
}

# =============================================================================
# Main
# =============================================================================

show_help() {
    cat << 'EOF'
Scalability Experiment Runner
=============================

Runs all scalability benchmark experiments with proper resource cleanup.

Usage:
  ./configs/scalability/run_experiments.sh [OPTIONS]

Options:
  --dry-run         Validate configs without actually running
  --resume          Skip already completed experiments
  --experiment X    Run only experiment X (e.g., mvr_32, conc_10)
  --force           Force re-run even if results exist
  --no-cleanup      Don't destroy infrastructure after each run
  --reset           Reset experiment state (clear completion history)
  --list            List all experiments and their status
  --help            Show this help message

Examples:
  # Run all experiments
  ./configs/scalability/run_experiments.sh

  # Dry run to validate configs
  ./configs/scalability/run_experiments.sh --dry-run

  # Resume after interruption
  ./configs/scalability/run_experiments.sh --resume

  # Run single experiment
  ./configs/scalability/run_experiments.sh --experiment mvr_32

  # Debug: run without cleanup
  ./configs/scalability/run_experiments.sh --experiment mvr_32 --no-cleanup

Experiments (in priority order):
  1. mvr_32   - 32GB single-node (ClickHouse failure threshold)
  2. conc_10  - 10 streams (concurrency cliff start)
  3. mvr_16   - 16GB extreme constraint
  4. conc_15  - 15 streams (more concurrency)
  5. node_1   - 1-node baseline (32GB)
  6. mvr_64   - 64GB (ClickHouse success threshold)
  7. conc_20  - 20 streams (high concurrency)
  8. node_2   - 2-node cluster (64GB total)
  9. node_4   - 4-node cluster (128GB total)

EOF
}

list_experiments() {
    echo ""
    echo "Scalability Experiments Status"
    echo "=============================="
    echo ""
    printf "%-12s %-15s %-20s\n" "EXPERIMENT" "STATUS" "CONFIG FILE"
    printf "%-12s %-15s %-20s\n" "----------" "------" "-----------"

    for experiment in "${EXPERIMENTS[@]}"; do
        local status=$(get_experiment_status "$experiment")
        local config="${CONFIG_DIR}/${experiment}.yaml"
        local config_status="✓"

        [[ ! -f "$config" ]] && config_status="✗ MISSING"
        [[ -z "$status" ]] && status="pending"

        printf "%-12s %-15s %-20s\n" "$experiment" "$status" "${config_status}"
    done
    echo ""
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
            --force)
                FORCE=true
                shift
                ;;
            --no-cleanup)
                NO_CLEANUP=true
                shift
                ;;
            --experiment)
                SINGLE_EXPERIMENT="$2"
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

    log_section "Scalability Experiment Runner"
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

    # Check config directory exists
    if [[ ! -d "$CONFIG_DIR" ]]; then
        die "Config directory not found: ${CONFIG_DIR}"
    fi

    # Determine which experiments to run
    local experiments_to_run=()

    if [[ -n "$SINGLE_EXPERIMENT" ]]; then
        # Validate the experiment name
        local valid=false
        for exp in "${EXPERIMENTS[@]}"; do
            if [[ "$exp" == "$SINGLE_EXPERIMENT" ]]; then
                valid=true
                break
            fi
        done

        if ! $valid; then
            die "Unknown experiment: ${SINGLE_EXPERIMENT}. Use --list to see available experiments."
        fi

        experiments_to_run=("$SINGLE_EXPERIMENT")
    else
        experiments_to_run=("${EXPERIMENTS[@]}")
    fi

    log INFO "Experiments to run: ${experiments_to_run[*]}"

    # Run experiments
    local total=${#experiments_to_run[@]}
    local completed=0
    local failed=0
    local skipped=0

    for i in "${!experiments_to_run[@]}"; do
        local experiment="${experiments_to_run[$i]}"
        local num=$((i + 1))

        log INFO "Progress: ${num}/${total} - Starting ${experiment}"

        if run_experiment "$experiment"; then
            ((completed++))
        else
            local status=$(get_experiment_status "$experiment")
            if [[ "$status" == "completed" ]]; then
                ((skipped++))
            else
                ((failed++))
            fi
        fi

        # Brief pause between experiments
        if [[ $num -lt $total ]] && ! $DRY_RUN; then
            log INFO "Waiting 30 seconds before next experiment..."
            sleep 30
        fi
    done

    # Aggregate results
    aggregate_results

    if ! $DRY_RUN; then
        collect_benchmark_data
    fi

    # Final summary
    log_section "Experiment Run Complete"
    log INFO "Total experiments: ${total}"
    log INFO "Completed: ${completed}"
    log INFO "Skipped: ${skipped}"
    log INFO "Failed: ${failed}"

    if [[ $failed -gt 0 ]]; then
        log WARN "Some experiments failed. Check logs in ${LOG_DIR}/"
        exit 1
    fi

    log INFO "All experiments completed successfully!"
    exit 0
}

main "$@"
