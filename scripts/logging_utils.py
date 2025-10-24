"""
ABOUTME: Comprehensive logging utility with color-coded output
ABOUTME: Provides consistent logging across all data processing scripts
"""

import sys
from datetime import datetime
from typing import Optional

class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Logger:
    """Enhanced logger with color-coded output and timestamps"""
    
    def __init__(self, script_name: str, verbose: bool = True):
        self.script_name = script_name
        self.verbose = verbose
        self.start_time = datetime.now()
        self.error_count = 0
        self.warning_count = 0
        
    def _format_time(self) -> str:
        """Get formatted timestamp"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _log(self, level: str, message: str, color: str = ""):
        """Internal logging method"""
        timestamp = self._format_time()
        prefix = f"[{timestamp}] [{self.script_name}] [{level}]"
        
        if color:
            print(f"{color}{prefix} {message}{Colors.ENDC}")
        else:
            print(f"{prefix} {message}")
        
        sys.stdout.flush()
    
    def header(self, message: str):
        """Print a prominent header"""
        separator = "=" * 80
        print(f"\n{Colors.HEADER}{Colors.BOLD}{separator}")
        print(f"  {message}")
        print(f"{separator}{Colors.ENDC}\n")
        sys.stdout.flush()
    
    def info(self, message: str):
        """Log informational message"""
        if self.verbose:
            self._log("INFO", message, Colors.OKBLUE)
    
    def success(self, message: str):
        """Log success message"""
        self._log("SUCCESS", message, Colors.OKGREEN)
    
    def warning(self, message: str):
        """Log warning message"""
        self.warning_count += 1
        self._log("WARNING", message, Colors.WARNING)
    
    def error(self, message: str, exception: Optional[Exception] = None):
        """Log error message"""
        self.error_count += 1
        self._log("ERROR", message, Colors.FAIL)
        if exception and self.verbose:
            print(f"{Colors.FAIL}  └─ Exception: {str(exception)}{Colors.ENDC}")
            sys.stdout.flush()
    
    def critical(self, message: str):
        """Log critical error and exit"""
        self._log("CRITICAL", message, f"{Colors.FAIL}{Colors.BOLD}")
        sys.exit(1)
    
    def debug(self, message: str):
        """Log debug message (only in verbose mode)"""
        if self.verbose:
            self._log("DEBUG", message, Colors.OKCYAN)
    
    def section(self, title: str):
        """Print a section divider"""
        print(f"\n{Colors.BOLD}{Colors.OKCYAN}{'─' * 80}")
        print(f"  {title}")
        print(f"{'─' * 80}{Colors.ENDC}\n")
        sys.stdout.flush()
    
    def stats(self, stats_dict: dict):
        """Print statistics in a formatted way"""
        print(f"\n{Colors.BOLD}Statistics:{Colors.ENDC}")
        for key, value in stats_dict.items():
            print(f"  • {key}: {Colors.OKGREEN}{value}{Colors.ENDC}")
        print()
        sys.stdout.flush()
    
    def progress(self, current: int, total: int, message: str = ""):
        """Simple progress indicator"""
        percentage = (current / total * 100) if total > 0 else 0
        bar_length = 50
        filled = int(bar_length * current / total) if total > 0 else 0
        bar = '█' * filled + '░' * (bar_length - filled)
        
        status = f"[{current}/{total}] {percentage:.1f}%"
        if message:
            status += f" - {message}"
        
        print(f"\r{Colors.OKBLUE}{bar}{Colors.ENDC} {status}", end='', flush=True)
        
        if current >= total:
            print()  # New line when complete
    
    def summary(self):
        """Print execution summary"""
        elapsed = datetime.now() - self.start_time
        hours, remainder = divmod(elapsed.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        print(f"\n{Colors.BOLD}{Colors.HEADER}{'=' * 80}")
        print(f"  EXECUTION SUMMARY")
        print(f"{'=' * 80}{Colors.ENDC}")
        
        print(f"\n{Colors.BOLD}Script:{Colors.ENDC} {self.script_name}")
        print(f"{Colors.BOLD}Duration:{Colors.ENDC} {int(hours)}h {int(minutes)}m {int(seconds)}s")
        
        if self.error_count > 0:
            print(f"{Colors.FAIL}{Colors.BOLD}Errors:{Colors.ENDC} {self.error_count}")
        else:
            print(f"{Colors.OKGREEN}{Colors.BOLD}Errors:{Colors.ENDC} 0")
        
        if self.warning_count > 0:
            print(f"{Colors.WARNING}{Colors.BOLD}Warnings:{Colors.ENDC} {self.warning_count}")
        else:
            print(f"{Colors.OKGREEN}{Colors.BOLD}Warnings:{Colors.ENDC} 0")
        
        print(f"\n{Colors.HEADER}{'=' * 80}{Colors.ENDC}\n")
        sys.stdout.flush()


# Example usage
if __name__ == "__main__":
    logger = Logger("test_script", verbose=True)
    
    logger.header("Testing Logger Utility")
    logger.info("This is an info message")
    logger.success("This is a success message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.debug("This is a debug message")
    
    logger.section("Statistics Section")
    logger.stats({
        "Total Records": 1000,
        "Processed": 950,
        "Errors": 50,
        "Success Rate": "95%"
    })
    
    logger.section("Progress Test")
    for i in range(101):
        logger.progress(i, 100, f"Processing item {i}")
        import time
        time.sleep(0.02)
    
    logger.summary()
