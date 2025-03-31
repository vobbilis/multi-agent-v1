#!/bin/bash

set -e

# Define colors for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

function print_header() {
    echo -e "\n${BOLD}${BLUE}$1${NC}\n"
}

function print_success() {
    echo -e "${GREEN}$1${NC}"
}

function print_warning() {
    echo -e "${YELLOW}$1${NC}"
}

function print_error() {
    echo -e "${RED}$1${NC}"
}

function print_usage() {
    echo -e "${BOLD}Usage:${NC}"
    echo -e "  $0 <scenario-file-path> [--delete]"
    echo -e "\n${BOLD}Examples:${NC}"
    echo -e "  $0 resource-issues/memory-exhaustion.yaml"
    echo -e "  $0 application-issues/kafka-imbalance.yaml"
    echo -e "  $0 resource-issues/memory-exhaustion.yaml --delete"
    echo -e "\n${BOLD}Available scenarios:${NC}"
    find . -name "*.yaml" | sort | sed 's/.\//  /'
}

# Check if a scenario file was provided
if [ $# -lt 1 ]; then
    print_error "Error: No scenario file specified."
    print_usage
    exit 1
fi

SCENARIO_FILE=$1
DELETE_MODE=0

# Check for delete flag
if [ "$2" == "--delete" ]; then
    DELETE_MODE=1
fi

# Check if file exists
if [ ! -f "$SCENARIO_FILE" ]; then
    print_error "Error: Scenario file '$SCENARIO_FILE' not found."
    print_usage
    exit 1
fi

# Extract scenario name from file path
SCENARIO_NAME=$(basename "$SCENARIO_FILE" .yaml)
SCENARIO_DIR=$(dirname "$SCENARIO_FILE")
SCENARIO_CATEGORY=$(basename "$SCENARIO_DIR")

# Function to extract scenario info from ConfigMap
function extract_scenario_info() {
    local yaml_file=$1
    local info_type=$2
    
    # Extract the ConfigMap data section that contains the description
    # This is somewhat hacky but works for our scenario files
    sed -n '/kind: ConfigMap/,/^---/p' "$yaml_file" | 
        grep -A 100 "$info_type: |" | 
        grep -v "$info_type: |" | 
        sed '/^---/q' | 
        sed '/^---/d' | 
        sed 's/^  //'
}

# Function to check kubectl connection
function check_kubectl() {
    print_header "Checking connection to Kubernetes cluster..."
    if ! kubectl cluster-info &> /dev/null; then
        print_error "Error: Cannot connect to Kubernetes cluster. Please check your kubeconfig."
        exit 1
    fi
    print_success "Successfully connected to Kubernetes cluster."
    kubectl cluster-info | head -n 1
    echo ""
}

# Function to apply the scenario
function apply_scenario() {
    print_header "Applying scenario: $SCENARIO_CATEGORY/$SCENARIO_NAME"
    
    # Apply the YAML file
    kubectl apply -f "$SCENARIO_FILE"
    
    print_success "Scenario applied successfully."
}

# Function to delete the scenario
function delete_scenario() {
    print_header "Deleting scenario: $SCENARIO_CATEGORY/$SCENARIO_NAME"
    
    # Delete the YAML file
    kubectl delete -f "$SCENARIO_FILE" --ignore-not-found
    
    print_success "Scenario deleted successfully."
}

# Function to display scenario details
function display_scenario_details() {
    print_header "Scenario Details"
    
    description=$(extract_scenario_info "$SCENARIO_FILE" "description")
    symptoms=$(extract_scenario_info "$SCENARIO_FILE" "investigation-symptoms")
    
    echo -e "${BOLD}Category:${NC} $SCENARIO_CATEGORY"
    echo -e "${BOLD}Name:${NC} $SCENARIO_NAME"
    echo -e "\n${BOLD}Description:${NC}"
    echo "$description"
    
    echo -e "\n${BOLD}Expected Symptoms:${NC}"
    echo "$symptoms"
}

# Function to provide observation instructions
function provide_observation_instructions() {
    local namespace=$(grep "namespace:" "$SCENARIO_FILE" | head -1 | awk '{print $2}')
    
    if [ -z "$namespace" ]; then
        namespace="default"
    fi
    
    print_header "Observation Instructions"
    echo -e "To observe the scenario in action, you can use the following commands:"
    echo -e "\n${BOLD}1. Check pods in the scenario namespace:${NC}"
    echo -e "   kubectl get pods -n $namespace -w"
    
    echo -e "\n${BOLD}2. Check events in the scenario namespace:${NC}"
    echo -e "   kubectl get events -n $namespace --sort-by=.metadata.creationTimestamp"
    
    echo -e "\n${BOLD}3. Check logs of specific pods:${NC}"
    echo -e "   kubectl logs -n $namespace <pod-name>"
    
    echo -e "\n${BOLD}4. Describe resources for more details:${NC}"
    echo -e "   kubectl describe pod -n $namespace <pod-name>"
    
    # Add specific instructions based on scenario category
    case $SCENARIO_CATEGORY in
        "resource-issues")
            echo -e "\n${BOLD}5. Monitor resource usage:${NC}"
            echo -e "   kubectl top pods -n $namespace"
            echo -e "   kubectl top nodes"
            ;;
        "network-issues")
            echo -e "\n${BOLD}5. Check network policies:${NC}"
            echo -e "   kubectl get networkpolicies -n $namespace"
            echo -e "   kubectl describe networkpolicy -n $namespace <policy-name>"
            ;;
        "storage-issues")
            echo -e "\n${BOLD}5. Check PVCs and PVs:${NC}"
            echo -e "   kubectl get pvc -n $namespace"
            echo -e "   kubectl get pv"
            echo -e "   kubectl describe pvc -n $namespace <pvc-name>"
            ;;
        "application-issues")
            echo -e "\n${BOLD}5. Check services and endpoints:${NC}"
            echo -e "   kubectl get svc,ep -n $namespace"
            ;;
        "security-issues")
            echo -e "\n${BOLD}5. Check secrets and certificates:${NC}"
            echo -e "   kubectl get secrets -n $namespace"
            echo -e "   kubectl describe secret -n $namespace <secret-name>"
            ;;
        "control-plane-issues")
            echo -e "\n${BOLD}5. Check control plane components:${NC}"
            echo -e "   kubectl get pods -n kube-system"
            echo -e "   kubectl logs -n kube-system <control-plane-pod>"
            ;;
        *)
            echo -e "\n${BOLD}5. Check all resources in the namespace:${NC}"
            echo -e "   kubectl get all -n $namespace"
            ;;
    esac

    echo -e "\n${BOLD}To clean up this scenario:${NC}"
    echo -e "   $0 $SCENARIO_FILE --delete"
}

# Main execution
check_kubectl

if [ $DELETE_MODE -eq 1 ]; then
    delete_scenario
    exit 0
fi

display_scenario_details
apply_scenario
provide_observation_instructions

print_header "Test Root Cause Analysis"
echo -e "After the scenario has been running for a few minutes, you can test your Root Cause Analysis engine by:"
echo -e "1. Looking for the symptoms described above"
echo -e "2. Running your RCA engine against the affected namespace or components"
echo -e "3. Comparing the detected root cause with the expected root cause in the scenario description"

print_warning "\nRemember to clean up the scenario when finished:\n  $0 $SCENARIO_FILE --delete" 