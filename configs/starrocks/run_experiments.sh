#!/usr/bin/env bash
#
# StarRocks Experiment Runner (Parallel Edition)
# ==============================================
# Runs all Exasol vs StarRocks benchmark experiments with parallel execution
# and proper resource cleanup.
#
# Features:
# - Parallel execution with configurable concurrency
# - Phase-based grouping (SF1, SF10, SF30)
# - Automatic infrastructure cleanup after each experiment
# - Resume capability (skips completed experiments)
# - Thread-safe state management
# - Comprehensive logging (per-experiment logs)
# - Signal handling for graceful shutdown of parallel jobs
# - Timeout protection
# - Dry-run mode for validation
# - Real-time progress display
#
# Usage:
#   ./configs/starrocks/run_experiments.sh [OPTIONS]
#
# Options:
#   --dry-run         Validate configs without running
#   --resume          Skip already completed experiments
#   --experiment X    Run only experiment X (e.g., exa_vs_sr_1g)
#   --force           Force re-run even if results exist
#   --no-cleanup      Don't destroy infrastructure after each run
#   --parallel N      Run N experiments concurrently (default: 3)
#   --phase X         Run only phase X (1=SF1, 2=SF10, 3=SF30)
#   --sequential      Force sequential execution (original behavior)
#   --help            Show this help message
#

set -o pipefail

# =============================================================================
# Configuration
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
CONFIG_DIR="${SCRIPT_DIR}"
RESULTS_DIR="${REPO_ROOT}/results"
LOG_DIR="${REPO_ROOT}/logs/starrocks"
STATE_FILE="${LOG_DIR}/.experiment_state"

# Phase groupings by scale factor
PHASE_1=(
    "exa_vs_sr_1g"
    "exa_vs_sr_1g_mu5"
    "exa_vs_sr_1g_mu15"
    "exa_vs_sr_1g_mn"
    "exa_vs_sr_1g_mn_mu5"
    "exa_vs_sr_1g_mn_mu15"
)

PHASE_2=(
    "exa_vs_sr_10g"
    "exa_vs_sr_10g_mu5"
    "exa_vs_sr_10g_mu15"
    "exa_vs_sr_10g_mn"
    "exa_vs_sr_10g_mn_mu5"
    "exa_vs_sr_10g_mn_mu15"
)

PHASE_3=(
    "exa_vs_sr_30g"
    "exa_vs_sr_30g_mu5"
    "exa_vs_sr_30g_mu15"
    "exa_vs_sr_30g_mn"
    "exa_vs_sr_30g_mn_mu5"
    "exa_vs_sr_30g_mn_mu15"
)

# All experiments in priority order (for sequential mode)
EXPERIMENTS=(
    "${PHASE_1[@]}"
    "${PHASE_2[@]}"
    "${PHASE_3[@]}"
)

# Timeouts (in seconds)
INFRA_TIMEOUT=1800       # 30 minutes for infrastructure
BENCHMARK_TIMEOUT=10800  # 3 hours for benchmark run (larger for SF30)
DESTROY_TIMEOUT=600      # 10 minutes for cleanup

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# =============================================================================
# Global State
# =============================================================================

DRY_RUN=false
RESUME=false
FORCE=false
NO_CLEANUP=false
SEQUENTIAL=false
SINGLE_EXPERIMENT=""
SINGLE_PHASE=""
MAX_PARALLEL=3

# Parallel execution state
declare -A RUNNING_PIDS        # experiment_name -> PID
declare -A RUNNING_EXPERIMENTS # PID -> experiment_name
PARALLEL_MODE=false

# Sequential execution state (backward compatibility)
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
        PHASE) color="$MAGENTA" ;;
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
# Thread-Safe State Management
# =============================================================================

save_state() {
    local experiment="$1"
    local status="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    # Atomic write with file lock
    (
        flock -x 200
        echo "${experiment}|${status}|${timestamp}" >> "${STATE_FILE}"
    ) 200>"${STATE_FILE}.lock"
}

get_experiment_status() {
    local experiment="$1"
    if [[ -f "${STATE_FILE}" ]]; then
        # Use flock for safe reading too
        (
            flock -s 200
            grep "^${experiment}|" "${STATE_FILE}" | tail -1 | cut -d'|' -f2
        ) 200>"${STATE_FILE}.lock"
    fi
}

is_experiment_completed() {
    local experiment="$1"
    local status=$(get_experiment_status "$experiment")
    [[ "$status" == "completed" ]]
}

reset_state() {
    log INFO "Resetting experiment state..."
    rm -f "${STATE_FILE}" "${STATE_FILE}.lock"
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

    log INFO "[${experiment}] Destroying infrastructure..."

    if $DRY_RUN; then
        log INFO "[${experiment}] [DRY-RUN] Would destroy infrastructure"
        return 0
    fi

    # Run destroy with timeout
    timeout "${DESTROY_TIMEOUT}" python -m benchkit infra destroy -c "$config" \
        >> "$log_file" 2>&1
    local exit_code=$?

    if [[ $exit_code -eq 0 ]]; then
        log INFO "[${experiment}] Infrastructure destroyed successfully"
        return 0
    elif [[ $exit_code -eq 124 ]]; then
        log WARN "[${experiment}] Infrastructure destroy timed out after ${DESTROY_TIMEOUT}s"
        return 1
    else
        log WARN "[${experiment}] Infrastructure destroy failed (exit code: $exit_code)"
        return 1
    fi
}

force_cleanup() {
    local config="$1"
    local experiment="$2"

    log WARN "[${experiment}] Attempting force cleanup..."

    # Try destroy up to 3 times
    for attempt in 1 2 3; do
        log INFO "[${experiment}] Cleanup attempt ${attempt}/3..."
        if destroy_infrastructure "$config" "$experiment"; then
            return 0
        fi
        sleep 10
    done

    log ERROR "[${experiment}] Force cleanup failed after 3 attempts. Manual intervention may be required."
    return 1
}

# =============================================================================
# Experiment Execution
# =============================================================================

validate_config() {
    local config="$1"
    local experiment="$2"

    log INFO "[${experiment}] Validating config: ${config}"

    if [[ ! -f "$config" ]]; then
        log ERROR "[${experiment}] Config file not found: ${config}"
        return 1
    fi

    # Check required fields
    for field in project_id systems workload env; do
        if ! grep -q "^${field}:" "$config"; then
            log ERROR "[${experiment}] Missing required field '${field}' in ${config}"
            return 1
        fi
    done

    # Run benchkit check
    if ! python -m benchkit check -c "$config" > /dev/null 2>&1; then
        log WARN "[${experiment}] Config validation warning"
    fi

    log INFO "[${experiment}] Config validation passed"
    return 0
}

run_experiment_impl() {
    local experiment="$1"
    local config="${CONFIG_DIR}/${experiment}.yaml"
    local log_file="${LOG_DIR}/${experiment}.log"
    local start_time=$(date +%s)

    # Validate config
    if ! validate_config "$config" "$experiment"; then
        save_state "$experiment" "config_error"
        return 1
    fi

    if $DRY_RUN; then
        log INFO "[${experiment}] [DRY-RUN] Would run experiment"
        log INFO "[${experiment}] [DRY-RUN] Config: ${config}"
        return 0
    fi

    # Mark as started
    save_state "$experiment" "started"

    # Step 1: Provision infrastructure
    log INFO "[${experiment}] Step 1/3: Provisioning infrastructure..."
    echo "=== Infrastructure Provisioning ===" >> "$log_file"

    timeout "${INFRA_TIMEOUT}" python -m benchkit infra apply -c "$config" \
        >> "$log_file" 2>&1
    local infra_exit=$?

    if [[ $infra_exit -ne 0 ]]; then
        log ERROR "[${experiment}] Infrastructure provisioning failed (exit code: $infra_exit)"
        save_state "$experiment" "infra_failed"
        cleanup_experiment "$config" "$experiment"
        return 1
    fi
    log INFO "[${experiment}] Infrastructure provisioned successfully"

    # Step 2: Run full benchmark (setup + load + run)
    log INFO "[${experiment}] Step 2/3: Running benchmark (setup + load + run)..."
    echo "" >> "$log_file"
    echo "=== Benchmark Execution ===" >> "$log_file"

    timeout "${BENCHMARK_TIMEOUT}" python -m benchkit run --full -c "$config" \
        >> "$log_file" 2>&1
    local bench_exit=$?

    if [[ $bench_exit -ne 0 ]]; then
        if [[ $bench_exit -eq 124 ]]; then
            log ERROR "[${experiment}] Benchmark timed out after ${BENCHMARK_TIMEOUT}s"
            save_state "$experiment" "timeout"
        else
            log ERROR "[${experiment}] Benchmark failed (exit code: $bench_exit)"
            save_state "$experiment" "benchmark_failed"
        fi
        cleanup_experiment "$config" "$experiment"
        return 1
    fi
    log INFO "[${experiment}] Benchmark completed successfully"

    # Step 3: Cleanup infrastructure
    log INFO "[${experiment}] Step 3/3: Cleaning up infrastructure..."
    cleanup_experiment "$config" "$experiment"

    # Calculate duration
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    local duration_min=$((duration / 60))

    log INFO "[${experiment}] Completed in ${duration_min} minutes"
    save_state "$experiment" "completed"

    return 0
}

# Wrapper for sequential execution (maintains backward compatibility)
run_experiment() {
    local experiment="$1"

    log_section "Running Experiment: ${experiment}"

    # Check if already completed (resume mode)
    if $RESUME && is_experiment_completed "$experiment"; then
        log INFO "[${experiment}] Already completed, skipping..."
        return 0
    fi

    # Track for signal handling in sequential mode
    CURRENT_EXPERIMENT="$experiment"
    CLEANUP_NEEDED=true

    run_experiment_impl "$experiment"
    local result=$?

    CLEANUP_NEEDED=false
    CURRENT_EXPERIMENT=""

    return $result
}

# Async wrapper for parallel execution
run_experiment_async() {
    local experiment="$1"
    local log_file="${LOG_DIR}/${experiment}.log"

    # All output goes to experiment log file
    exec >> "$log_file" 2>&1

    log INFO "[${experiment}] Starting async execution (PID: $$)"
    run_experiment_impl "$experiment"
    exit $?
}

cleanup_experiment() {
    local config="$1"
    local experiment="$2"

    if $NO_CLEANUP; then
        log WARN "[${experiment}] Skipping cleanup (--no-cleanup flag set)"
        return 0
    fi

    if ! destroy_infrastructure "$config" "$experiment"; then
        force_cleanup "$config" "$experiment"
    fi
}

# =============================================================================
# Parallel Execution
# =============================================================================

wait_for_any_job() {
    # Wait for any background job to complete
    local completed_pid
    local completed_experiment

    while true; do
        for pid in "${!RUNNING_EXPERIMENTS[@]}"; do
            if ! kill -0 "$pid" 2>/dev/null; then
                completed_pid="$pid"
                completed_experiment="${RUNNING_EXPERIMENTS[$pid]}"
                break 2
            fi
        done
        sleep 1
    done

    # Get exit code
    wait "$completed_pid"
    local exit_code=$?

    # Update tracking
    unset RUNNING_EXPERIMENTS["$completed_pid"]
    unset RUNNING_PIDS["$completed_experiment"]

    # Log result
    if [[ $exit_code -eq 0 ]]; then
        log INFO "[${completed_experiment}] Completed successfully"
    else
        log ERROR "[${completed_experiment}] Failed with exit code ${exit_code}"
    fi

    return $exit_code
}

wait_for_all_jobs() {
    local failed=0

    log INFO "Waiting for ${#RUNNING_EXPERIMENTS[@]} running experiment(s) to complete..."

    while [[ ${#RUNNING_EXPERIMENTS[@]} -gt 0 ]]; do
        wait_for_any_job || ((failed++))
    done

    return $failed
}

run_phase() {
    local phase_name="$1"
    shift
    local experiments=("$@")
    local running=0
    local started=0
    local skipped=0
    local failed=0

    log_section "Phase: ${phase_name} (${#experiments[@]} experiments, max ${MAX_PARALLEL} parallel)"

    for experiment in "${experiments[@]}"; do
        # Skip completed experiments in resume mode
        if $RESUME && is_experiment_completed "$experiment"; then
            log INFO "[${experiment}] Skipping (already completed)"
            ((skipped++))
            continue
        fi

        # Wait if at max parallelism
        while [[ ${#RUNNING_EXPERIMENTS[@]} -ge $MAX_PARALLEL ]]; do
            log DEBUG "At max parallelism (${MAX_PARALLEL}), waiting for a slot..."
            wait_for_any_job || ((failed++))
        done

        # Launch experiment in background
        log INFO "[${experiment}] Launching (running: ${#RUNNING_EXPERIMENTS[@]}/${MAX_PARALLEL})"

        run_experiment_async "$experiment" &
        local pid=$!

        # Track the running experiment
        RUNNING_PIDS["$experiment"]=$pid
        RUNNING_EXPERIMENTS[$pid]="$experiment"
        ((started++))

        # Small delay to stagger starts
        sleep 2
    done

    # Wait for remaining jobs in this phase
    if [[ ${#RUNNING_EXPERIMENTS[@]} -gt 0 ]]; then
        log INFO "Waiting for remaining ${#RUNNING_EXPERIMENTS[@]} experiment(s) in phase..."
        wait_for_all_jobs || ((failed += $?))
    fi

    log PHASE "${phase_name} complete: started=${started}, skipped=${skipped}, failed=${failed}"

    return $failed
}

run_parallel_all() {
    local total_failed=0

    log_section "Parallel Execution Mode (max ${MAX_PARALLEL} concurrent)"
    log INFO "Phase 1: SF1 experiments (6 total)"
    log INFO "Phase 2: SF10 experiments (6 total)"
    log INFO "Phase 3: SF30 experiments (6 total)"
    echo ""

    # Run Phase 1: SF1
    run_phase "SF1 (Phase 1/3)" "${PHASE_1[@]}" || ((total_failed += $?))

    # Brief pause between phases
    if ! $DRY_RUN; then
        log INFO "Pausing 30 seconds between phases..."
        sleep 30
    fi

    # Run Phase 2: SF10
    run_phase "SF10 (Phase 2/3)" "${PHASE_2[@]}" || ((total_failed += $?))

    # Brief pause between phases
    if ! $DRY_RUN; then
        log INFO "Pausing 30 seconds between phases..."
        sleep 30
    fi

    # Run Phase 3: SF30
    run_phase "SF30 (Phase 3/3)" "${PHASE_3[@]}" || ((total_failed += $?))

    return $total_failed
}

run_single_phase() {
    local phase_num="$1"
    local phase_name
    local phase_experiments

    case "$phase_num" in
        1)
            phase_name="SF1 (Phase 1)"
            phase_experiments=("${PHASE_1[@]}")
            ;;
        2)
            phase_name="SF10 (Phase 2)"
            phase_experiments=("${PHASE_2[@]}")
            ;;
        3)
            phase_name="SF30 (Phase 3)"
            phase_experiments=("${PHASE_3[@]}")
            ;;
        *)
            die "Invalid phase number: ${phase_num}. Use 1, 2, or 3."
            ;;
    esac

    log_section "Running Single Phase: ${phase_name}"
    run_phase "$phase_name" "${phase_experiments[@]}"
    return $?
}

# =============================================================================
# Signal Handling
# =============================================================================

cleanup_parallel_jobs() {
    log WARN "Cleaning up ${#RUNNING_EXPERIMENTS[@]} running experiment(s)..."

    # Send TERM signal to all running experiments
    for pid in "${!RUNNING_EXPERIMENTS[@]}"; do
        local experiment="${RUNNING_EXPERIMENTS[$pid]}"
        if kill -0 "$pid" 2>/dev/null; then
            log WARN "[${experiment}] Terminating (PID: ${pid})"
            kill -TERM "$pid" 2>/dev/null
            save_state "$experiment" "interrupted"
        fi
    done

    # Wait for graceful shutdown (max 10 seconds)
    local wait_count=0
    while [[ ${#RUNNING_EXPERIMENTS[@]} -gt 0 ]] && [[ $wait_count -lt 10 ]]; do
        for pid in "${!RUNNING_EXPERIMENTS[@]}"; do
            if ! kill -0 "$pid" 2>/dev/null; then
                unset RUNNING_EXPERIMENTS["$pid"]
            fi
        done
        sleep 1
        ((wait_count++))
    done

    # Force kill any remaining
    for pid in "${!RUNNING_EXPERIMENTS[@]}"; do
        local experiment="${RUNNING_EXPERIMENTS[$pid]}"
        if kill -0 "$pid" 2>/dev/null; then
            log WARN "[${experiment}] Force killing (PID: ${pid})"
            kill -9 "$pid" 2>/dev/null
        fi
    done

    # Cleanup infrastructure for all interrupted experiments
    log INFO "Cleaning up infrastructure for interrupted experiments..."
    for experiment in "${!RUNNING_PIDS[@]}"; do
        local config="${CONFIG_DIR}/${experiment}.yaml"
        if [[ -f "$config" ]]; then
            force_cleanup "$config" "$experiment" &
        fi
    done
    wait
}

cleanup_sequential_job() {
    if $CLEANUP_NEEDED && [[ -n "$CURRENT_EXPERIMENT" ]]; then
        log WARN "Cleaning up running experiment: ${CURRENT_EXPERIMENT}"
        local config="${CONFIG_DIR}/${CURRENT_EXPERIMENT}.yaml"

        save_state "$CURRENT_EXPERIMENT" "interrupted"

        if ! $DRY_RUN; then
            force_cleanup "$config" "$CURRENT_EXPERIMENT"
        fi
    fi
}

cleanup_on_exit() {
    local exit_code=$?

    echo ""
    log WARN "Received interrupt signal..."

    if $PARALLEL_MODE; then
        cleanup_parallel_jobs
    else
        cleanup_sequential_job
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
# StarRocks Experiment Results Summary

| Experiment | Status | Notes |
|------------|--------|-------|
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

        echo "| ${experiment} | ${status_emoji} ${status:-pending} | |" >> "$summary_file"
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
            local project_id="starrocks_${experiment}"
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
# Progress Display
# =============================================================================

show_parallel_status() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║  StarRocks Parallel Experiment Runner - Status                   ║"
    echo "╠══════════════════════════════════════════════════════════════════╣"

    for experiment in "${!RUNNING_PIDS[@]}"; do
        local pid="${RUNNING_PIDS[$experiment]}"
        local status="🔄 Running"

        if ! kill -0 "$pid" 2>/dev/null; then
            if is_experiment_completed "$experiment"; then
                status="✅ Completed"
            else
                status="❌ Failed"
            fi
        fi

        printf "║  %-40s %s         ║\n" "$experiment" "$status"
    done

    if [[ ${#RUNNING_PIDS[@]} -eq 0 ]]; then
        echo "║  No experiments currently running                               ║"
    fi

    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo ""
}

# =============================================================================
# Main
# =============================================================================

show_help() {
    cat << 'EOF'
StarRocks Experiment Runner (Parallel Edition)
==============================================

Runs all Exasol vs StarRocks benchmark experiments with parallel execution
and proper resource cleanup.

Usage:
  ./configs/starrocks/run_experiments.sh [OPTIONS]

Options:
  --dry-run         Validate configs without actually running
  --resume          Skip already completed experiments
  --experiment X    Run only experiment X (e.g., exa_vs_sr_1g)
  --force           Force re-run even if results exist
  --no-cleanup      Don't destroy infrastructure after each run
  --parallel N      Run N experiments concurrently (default: 3)
  --phase X         Run only phase X (1=SF1, 2=SF10, 3=SF30)
  --sequential      Force sequential execution (original behavior)
  --reset           Reset experiment state (clear completion history)
  --list            List all experiments and their status
  --status          Show current running experiments status
  --help            Show this help message

Execution Modes:
  Default (Parallel):  Runs experiments in 3 phases with up to 3 concurrent
  --sequential:        Runs all experiments one at a time (original behavior)
  --phase X:           Runs only the specified phase in parallel

Phase Groupings:
  Phase 1 (SF1):   6 experiments at scale factor 1 (fastest, ~40 min)
  Phase 2 (SF10):  6 experiments at scale factor 10 (~45 min)
  Phase 3 (SF30):  6 experiments at scale factor 30 (slowest, ~50 min)

Examples:
  # Run all experiments in parallel (default: 3 concurrent)
  ./configs/starrocks/run_experiments.sh

  # Run with higher parallelism
  ./configs/starrocks/run_experiments.sh --parallel 4

  # Dry run to validate all configs
  ./configs/starrocks/run_experiments.sh --dry-run

  # Resume interrupted parallel run
  ./configs/starrocks/run_experiments.sh --resume

  # Run only SF1 experiments in parallel
  ./configs/starrocks/run_experiments.sh --phase 1

  # Run only SF1 with 2 concurrent experiments
  ./configs/starrocks/run_experiments.sh --phase 1 --parallel 2

  # Run in sequential mode (original behavior)
  ./configs/starrocks/run_experiments.sh --sequential

  # Run single experiment
  ./configs/starrocks/run_experiments.sh --experiment exa_vs_sr_1g

  # Check logs for parallel experiments
  tail -f logs/starrocks/*.log

Experiments by Phase:

  Phase 1 - SF1 (Scale Factor 1):
    1. exa_vs_sr_1g           - Single-node, single-user
    2. exa_vs_sr_1g_mu5       - Single-node, 5 streams
    3. exa_vs_sr_1g_mu15      - Single-node, 15 streams
    4. exa_vs_sr_1g_mn        - Multi-node, single-user
    5. exa_vs_sr_1g_mn_mu5    - Multi-node, 5 streams
    6. exa_vs_sr_1g_mn_mu15   - Multi-node, 15 streams

  Phase 2 - SF10 (Scale Factor 10):
    7. exa_vs_sr_10g          - Single-node, single-user
    8. exa_vs_sr_10g_mu5      - Single-node, 5 streams
    9. exa_vs_sr_10g_mu15     - Single-node, 15 streams
   10. exa_vs_sr_10g_mn       - Multi-node, single-user
   11. exa_vs_sr_10g_mn_mu5   - Multi-node, 5 streams
   12. exa_vs_sr_10g_mn_mu15  - Multi-node, 15 streams

  Phase 3 - SF30 (Scale Factor 30):
   13. exa_vs_sr_30g          - Single-node, single-user
   14. exa_vs_sr_30g_mu5      - Single-node, 5 streams
   15. exa_vs_sr_30g_mu15     - Single-node, 15 streams
   16. exa_vs_sr_30g_mn       - Multi-node, single-user
   17. exa_vs_sr_30g_mn_mu5   - Multi-node, 5 streams
   18. exa_vs_sr_30g_mn_mu15  - Multi-node, 15 streams

AWS Resource Considerations:
  - Single-node experiments: 2 instances each (Exasol + StarRocks)
  - Multi-node experiments: 6 instances each (3 Exasol + 3 StarRocks)
  - Running 3 parallel: typically 6-18 instances
  - Default AWS limits: 20-50 instances per region (safe with --parallel 3)

EOF
}

list_experiments() {
    echo ""
    echo "StarRocks Experiments Status"
    echo "============================"
    echo ""
    printf "%-25s %-15s %-15s\n" "EXPERIMENT" "STATUS" "CONFIG"
    printf "%-25s %-15s %-15s\n" "-------------------------" "---------------" "------"

    for experiment in "${EXPERIMENTS[@]}"; do
        local status=$(get_experiment_status "$experiment")
        local config="${CONFIG_DIR}/${experiment}.yaml"
        local config_status="✓"

        [[ ! -f "$config" ]] && config_status="✗ MISSING"
        [[ -z "$status" ]] && status="pending"

        printf "%-25s %-15s %-15s\n" "$experiment" "$status" "${config_status}"
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
            --sequential)
                SEQUENTIAL=true
                shift
                ;;
            --parallel)
                MAX_PARALLEL="$2"
                if ! [[ "$MAX_PARALLEL" =~ ^[0-9]+$ ]] || [[ "$MAX_PARALLEL" -lt 1 ]]; then
                    die "Invalid parallel count: ${MAX_PARALLEL}. Must be a positive integer."
                fi
                shift 2
                ;;
            --phase)
                SINGLE_PHASE="$2"
                if ! [[ "$SINGLE_PHASE" =~ ^[123]$ ]]; then
                    die "Invalid phase: ${SINGLE_PHASE}. Use 1, 2, or 3."
                fi
                shift 2
                ;;
            --experiment)
                SINGLE_EXPERIMENT="$2"
                shift 2
                ;;
            --reset)
                ensure_dir "$LOG_DIR"
                reset_state
                exit 0
                ;;
            --list)
                ensure_dir "$LOG_DIR"
                list_experiments
                exit 0
                ;;
            --status)
                ensure_dir "$LOG_DIR"
                show_parallel_status
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

run_sequential_mode() {
    local experiments_to_run=("$@")
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

    echo ""
    log INFO "Sequential execution complete"
    log INFO "  Completed: ${completed}"
    log INFO "  Skipped: ${skipped}"
    log INFO "  Failed: ${failed}"

    return $failed
}

main() {
    parse_args "$@"

    # Setup logging
    ensure_dir "$LOG_DIR"

    log_section "StarRocks Experiment Runner"
    log INFO "Repository root: ${REPO_ROOT}"
    log INFO "Config directory: ${CONFIG_DIR}"
    log INFO "Results directory: ${RESULTS_DIR}"
    log INFO "Log directory: ${LOG_DIR}"
    log INFO ""
    log INFO "Options:"
    log INFO "  Dry run: ${DRY_RUN}"
    log INFO "  Resume mode: ${RESUME}"
    log INFO "  No cleanup: ${NO_CLEANUP}"
    log INFO "  Sequential mode: ${SEQUENTIAL}"
    log INFO "  Max parallel: ${MAX_PARALLEL}"
    [[ -n "$SINGLE_PHASE" ]] && log INFO "  Single phase: ${SINGLE_PHASE}"
    [[ -n "$SINGLE_EXPERIMENT" ]] && log INFO "  Single experiment: ${SINGLE_EXPERIMENT}"

    # Verify we're in the right directory
    if [[ ! -f "${REPO_ROOT}/pyproject.toml" ]]; then
        die "Script must be run from the benchkit repository"
    fi

    local failed=0

    # Handle single experiment mode (always sequential)
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

        log INFO "Running single experiment: ${SINGLE_EXPERIMENT}"
        run_sequential_mode "$SINGLE_EXPERIMENT"
        failed=$?

    # Handle single phase mode (parallel within phase)
    elif [[ -n "$SINGLE_PHASE" ]]; then
        PARALLEL_MODE=true
        run_single_phase "$SINGLE_PHASE"
        failed=$?

    # Handle sequential mode
    elif $SEQUENTIAL; then
        log INFO "Running in sequential mode"
        run_sequential_mode "${EXPERIMENTS[@]}"
        failed=$?

    # Default: parallel mode with phases
    else
        PARALLEL_MODE=true
        run_parallel_all
        failed=$?
    fi

    # Aggregate results
    aggregate_results

    if ! $DRY_RUN; then
        collect_benchmark_data
    fi

    # Final summary
    log_section "Experiment Run Complete"

    if [[ $failed -gt 0 ]]; then
        log WARN "Some experiments failed. Check logs in ${LOG_DIR}/"
        exit 1
    fi

    log INFO "All experiments completed successfully!"
    exit 0
}

main "$@"
