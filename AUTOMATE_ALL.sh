#!/bin/bash

# AUTOMATE_ALL.sh - Master Automation Script for Talent Intelligence System
# 
# This script runs all enrichment scripts, quality checks, and generates reports
# Can be scheduled via cron for weekly runs
#
# Usage:
#   ./AUTOMATE_ALL.sh                    # Run all operations
#   ./AUTOMATE_ALL.sh --enrichment-only  # Run only enrichment scripts
#   ./AUTOMATE_ALL.sh --quality-only     # Run only quality checks
#   ./AUTOMATE_ALL.sh --github-only      # Run only GitHub automation
#   ./AUTOMATE_ALL.sh --dry-run          # Show what would be run without executing
#
# Author: Talent Intelligence System
# Date: October 21, 2025
# Version: 1.0.0

set -e  # Exit on any error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/automation_$TIMESTAMP.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse command line arguments
ENRICHMENT_ONLY=false
QUALITY_ONLY=false
GITHUB_ONLY=false
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --enrichment-only)
            ENRICHMENT_ONLY=true
            shift
            ;;
        --quality-only)
            QUALITY_ONLY=true
            shift
            ;;
        --github-only)
            GITHUB_ONLY=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --enrichment-only  Run only enrichment scripts"
            echo "  --quality-only     Run only quality checks"
            echo "  --github-only      Run only GitHub automation"
            echo "  --dry-run          Show what would be run without executing"
            echo "  -h, --help         Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Logging function
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] ✅ $1${NC}" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️  $1${NC}" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ❌ $1${NC}" | tee -a "$LOG_FILE"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check PostgreSQL
    if ! command_exists psql; then
        log_error "PostgreSQL client (psql) not found. Please install PostgreSQL."
        exit 1
    fi
    
    # Check if PostgreSQL is running
    if ! pg_isready -q; then
        log_error "PostgreSQL is not running. Please start PostgreSQL."
        exit 1
    fi
    
    # Check if database exists
    if ! psql -d talent -c "SELECT 1;" >/dev/null 2>&1; then
        log_error "Database 'talent' not found or not accessible."
        exit 1
    fi
    
    # Check Python
    if ! command_exists python3; then
        log_error "Python 3 not found. Please install Python 3.8+."
        exit 1
    fi
    
    # Check required Python packages
    if ! python3 -c "import psycopg2" >/dev/null 2>&1; then
        log_error "psycopg2 not found. Please install: pip install psycopg2-binary"
        exit 1
    fi
    
    log_success "All prerequisites met"
}

# Function to run enrichment scripts
run_enrichment() {
    log "Starting enrichment scripts..."
    
    if [ "$DRY_RUN" = true ]; then
        log "DRY RUN: Would run enrichment scripts"
        log "  - cd enrichment_scripts && ./RUN_ALL_ENRICHMENTS.sh"
        return 0
    fi
    
    # Check if enrichment scripts directory exists
    if [ ! -d "enrichment_scripts" ]; then
        log_warning "enrichment_scripts directory not found, skipping enrichment"
        return 0
    fi
    
    # Run enrichment scripts
    cd enrichment_scripts
    if [ -f "RUN_ALL_ENRICHMENTS.sh" ]; then
        log "Running enrichment scripts..."
        if ./RUN_ALL_ENRICHMENTS.sh >> "$LOG_FILE" 2>&1; then
            log_success "Enrichment scripts completed successfully"
        else
            log_error "Enrichment scripts failed"
            return 1
        fi
    else
        log_warning "RUN_ALL_ENRICHMENTS.sh not found in enrichment_scripts/"
    fi
    
    cd "$SCRIPT_DIR"
}

# Function to run GitHub automation
run_github_automation() {
    log "Starting GitHub automation..."
    
    if [ "$DRY_RUN" = true ]; then
        log "DRY RUN: Would run GitHub automation"
        log "  - python3 enrich_github_continuous.py --batch-size 500 --with-matching"
        return 0
    fi
    
    # Check if GitHub automation script exists
    if [ ! -f "enrich_github_continuous.py" ]; then
        log_warning "enrich_github_continuous.py not found, skipping GitHub automation"
        return 0
    fi
    
    # Check if GitHub token is set
    if [ -z "$GITHUB_TOKEN" ]; then
        log_warning "GITHUB_TOKEN not set, GitHub automation will run with limited rate limits"
    fi
    
    # Run GitHub automation with moderate batch size
    log "Running GitHub automation (batch size: 500)..."
    if python3 enrich_github_continuous.py --batch-size 500 --with-matching >> "$LOG_FILE" 2>&1; then
        log_success "GitHub automation completed successfully"
    else
        log_error "GitHub automation failed"
        return 1
    fi
}

# Function to run quality checks
run_quality_checks() {
    log "Starting quality checks..."
    
    if [ "$DRY_RUN" = true ]; then
        log "DRY RUN: Would run quality checks"
        log "  - python3 generate_quality_metrics.py"
        log "  - python3 check_data_quality.py"
        log "  - python3 generate_audit_report.py"
        return 0
    fi
    
    # Generate quality metrics
    if [ -f "generate_quality_metrics.py" ]; then
        log "Generating quality metrics..."
        if python3 generate_quality_metrics.py >> "$LOG_FILE" 2>&1; then
            log_success "Quality metrics generated successfully"
        else
            log_error "Quality metrics generation failed"
            return 1
        fi
    else
        log_warning "generate_quality_metrics.py not found"
    fi
    
    # Run data quality checks
    if [ -f "check_data_quality.py" ]; then
        log "Running data quality checks..."
        if python3 check_data_quality.py >> "$LOG_FILE" 2>&1; then
            log_success "Data quality checks completed successfully"
        else
            log_error "Data quality checks failed"
            return 1
        fi
    else
        log_warning "check_data_quality.py not found"
    fi
    
    # Generate audit report
    if [ -f "generate_audit_report.py" ]; then
        log "Generating audit report..."
        if python3 generate_audit_report.py >> "$LOG_FILE" 2>&1; then
            log_success "Audit report generated successfully"
        else
            log_error "Audit report generation failed"
            return 1
        fi
    else
        log_warning "generate_audit_report.py not found"
    fi
}

# Function to generate summary report
generate_summary() {
    log "Generating automation summary..."
    
    local summary_file="$LOG_DIR/automation_summary_$TIMESTAMP.txt"
    
    cat > "$summary_file" << EOF
TALENT INTELLIGENCE AUTOMATION SUMMARY
=====================================
Date: $(date)
Log File: $LOG_FILE
Script: $0
Arguments: $*

SYSTEM STATUS
------------
Database: $(psql -d talent -t -c "SELECT 'Connected to ' || current_database() || ' on ' || inet_server_addr() || ':' || inet_server_port();" 2>/dev/null || echo "Database connection failed")

RECENT ACTIVITY
---------------
EOF
    
    # Add recent log entries to summary
    if [ -f "$LOG_FILE" ]; then
        tail -20 "$LOG_FILE" >> "$summary_file"
    fi
    
    log_success "Summary report generated: $summary_file"
}

# Function to cleanup old logs
cleanup_logs() {
    log "Cleaning up old log files..."
    
    # Keep only last 30 days of logs
    find "$LOG_DIR" -name "automation_*.log" -mtime +30 -delete 2>/dev/null || true
    find "$LOG_DIR" -name "automation_summary_*.txt" -mtime +30 -delete 2>/dev/null || true
    
    log_success "Log cleanup completed"
}

# Main execution function
main() {
    log "=========================================="
    log "TALENT INTELLIGENCE AUTOMATION STARTED"
    log "=========================================="
    log "Timestamp: $TIMESTAMP"
    log "Script Directory: $SCRIPT_DIR"
    log "Log File: $LOG_FILE"
    
    if [ "$DRY_RUN" = true ]; then
        log "DRY RUN MODE - No actual operations will be performed"
    fi
    
    # Check prerequisites
    check_prerequisites
    
    # Determine what to run based on arguments
    if [ "$ENRICHMENT_ONLY" = true ]; then
        log "Running enrichment-only mode"
        run_enrichment
    elif [ "$QUALITY_ONLY" = true ]; then
        log "Running quality-only mode"
        run_quality_checks
    elif [ "$GITHUB_ONLY" = true ]; then
        log "Running GitHub-only mode"
        run_github_automation
    else
        log "Running full automation mode"
        
        # Run enrichment scripts
        run_enrichment
        
        # Run GitHub automation
        run_github_automation
        
        # Run quality checks
        run_quality_checks
    fi
    
    # Generate summary
    generate_summary
    
    # Cleanup old logs
    cleanup_logs
    
    log "=========================================="
    log "TALENT INTELLIGENCE AUTOMATION COMPLETED"
    log "=========================================="
    log_success "Automation completed successfully!"
    log "Check log file for details: $LOG_FILE"
}

# Error handling
trap 'log_error "Script interrupted or failed at line $LINENO"; exit 1' INT TERM ERR

# Run main function
main "$@"
