#!/usr/bin/env bash
#
# setup_ips.sh — Generate suite configs from templates using Terraform IPs
#
# Usage:
#   1. benchkit infra apply -c configs/remote_test/infra.yaml
#   2. bash configs/remote_test/setup_ips.sh
#
# Reads terraform output from results/remote_test_infra/terraform/,
# then generates configs in remote/ from templates/ with real IPs.
# Safe to run multiple times — always regenerates from templates.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TEMPLATE_DIR="$SCRIPT_DIR/templates"
CONFIG_DIR="$SCRIPT_DIR/remote"
TF_STATE_DIR="$REPO_ROOT/results/remote_test_infra/terraform"
INFRA_CONFIG="$SCRIPT_DIR/infra.yaml"

# --- Helpers ---

die() { echo "ERROR: $*" >&2; exit 1; }

json_get() {
    echo "$1" | python3 -c "import sys,json; d=json.load(sys.stdin); print($2)"
}

# --- Pre-checks ---

[[ -d "$TF_STATE_DIR" ]] || die "Terraform state not found at $TF_STATE_DIR
Run first: benchkit infra apply -c $INFRA_CONFIG"

[[ -d "$TEMPLATE_DIR" ]] || die "Templates directory not found at $TEMPLATE_DIR"

command -v terraform >/dev/null 2>&1 || die "terraform not found in PATH"

# --- Extract IPs from Terraform ---

echo "Reading Terraform outputs from $TF_STATE_DIR ..."
TF_JSON="$(terraform -chdir="$TF_STATE_DIR" output -json 2>/dev/null)" \
    || die "Failed to read terraform output"

EXASOL_PUB="$(json_get  "$TF_JSON" "d['system_public_ips']['value']['exasol'][0]")"
EXASOL_PRIV="$(json_get "$TF_JSON" "d['system_private_ips']['value']['exasol'][0]")"
CH_PUB="$(json_get      "$TF_JSON" "d['system_public_ips']['value']['clickhouse'][0]")"
EXA_MN0_PUB="$(json_get  "$TF_JSON" "d['system_public_ips']['value']['exasol_mn'][0]")"
EXA_MN0_PRIV="$(json_get "$TF_JSON" "d['system_private_ips']['value']['exasol_mn'][0]")"
EXA_MN1_PUB="$(json_get  "$TF_JSON" "d['system_public_ips']['value']['exasol_mn'][1]")"
EXA_MN1_PRIV="$(json_get "$TF_JSON" "d['system_private_ips']['value']['exasol_mn'][1]")"

SSH_KEY="$(python3 -c "
import yaml, os.path
with open('$INFRA_CONFIG') as f:
    cfg = yaml.safe_load(f)
print(os.path.expanduser(cfg['env']['ssh_private_key_path']))
")"

echo ""
echo "Extracted IPs:"
echo "  exasol:       public=$EXASOL_PUB  private=$EXASOL_PRIV"
echo "  clickhouse:   public=$CH_PUB"
echo "  exasol_mn[0]: public=$EXA_MN0_PUB  private=$EXA_MN0_PRIV"
echo "  exasol_mn[1]: public=$EXA_MN1_PUB  private=$EXA_MN1_PRIV"
echo "  ssh_key:      $SSH_KEY"
echo ""

# --- Generate configs from templates ---

mkdir -p "$CONFIG_DIR"

echo "Generating configs from templates/ -> remote/ ..."
for tmpl in "$TEMPLATE_DIR"/*.yaml; do
    fname="$(basename "$tmpl")"
    out="$CONFIG_DIR/$fname"

    sed \
        -e "s|{{EXASOL_PUB}}|$EXASOL_PUB|g" \
        -e "s|{{EXASOL_PRIV}}|$EXASOL_PRIV|g" \
        -e "s|{{CH_PUB}}|$CH_PUB|g" \
        -e "s|{{EXA_MN0_PUB}}|$EXA_MN0_PUB|g" \
        -e "s|{{EXA_MN0_PRIV}}|$EXA_MN0_PRIV|g" \
        -e "s|{{EXA_MN1_PUB}}|$EXA_MN1_PUB|g" \
        -e "s|{{EXA_MN1_PRIV}}|$EXA_MN1_PRIV|g" \
        -e "s|{{SSH_KEY}}|$SSH_KEY|g" \
        "$tmpl" > "$out"

    echo "  $fname"
done

echo ""
echo "Done. Verify with:"
echo "  benchkit suite status configs/remote_test/"
