"""
ABOUTME: Advanced progress reporting with ETA calculation
ABOUTME: Provides detailed progress tracking for long-running operations
"""

import time
from datetime import datetime, timedelta
from typing import Optional


class ProgressReporter:
    """
    Advanced progress reporter with ETA, speed tracking, and visual progress bars
    """
    
    def __init__(self, total: int, task_name: str = "Processing", 
                 show_speed: bool = True, bar_length: int = 50):
        self.total = total
        self.current = 0
        self.task_name = task_name
        self.show_speed = show_speed
        self.bar_length = bar_length
        
        self.start_time = time.time()
        self.last_update_time = self.start_time
        self.checkpoint_time = self.start_time
        self.checkpoint_count = 0
        
        # Track recent speed for smoother ETA
        self.speed_samples = []
        self.max_samples = 10
        
    def update(self, increment: int = 1, message: str = ""):
        """Update progress by increment and display status"""
        self.current += increment
        current_time = time.time()
        
        # Calculate speed (items per second)
        elapsed = current_time - self.checkpoint_time
        if elapsed > 0:
            speed = (self.current - self.checkpoint_count) / elapsed
            self.speed_samples.append(speed)
            if len(self.speed_samples) > self.max_samples:
                self.speed_samples.pop(0)
        
        # Update checkpoint every 10 items or 1 second
        if self.current - self.checkpoint_count >= 10 or elapsed > 1.0:
            self.checkpoint_time = current_time
            self.checkpoint_count = self.current
        
        # Display progress
        self._display(message)
    
    def set_progress(self, current: int, message: str = ""):
        """Set absolute progress value"""
        self.current = current
        self._display(message)
    
    def _display(self, message: str = ""):
        """Display progress bar with stats"""
        percentage = (self.current / self.total * 100) if self.total > 0 else 0
        
        # Create progress bar
        filled = int(self.bar_length * self.current / self.total) if self.total > 0 else 0
        bar = '█' * filled + '░' * (self.bar_length - filled)
        
        # Calculate stats
        elapsed = time.time() - self.start_time
        avg_speed = sum(self.speed_samples) / len(self.speed_samples) if self.speed_samples else 0
        
        # Calculate ETA
        if avg_speed > 0 and self.current < self.total:
            remaining_items = self.total - self.current
            eta_seconds = remaining_items / avg_speed
            eta = str(timedelta(seconds=int(eta_seconds)))
        else:
            eta = "N/A"
        
        # Format elapsed time
        elapsed_str = str(timedelta(seconds=int(elapsed)))
        
        # Build status line
        status_parts = [
            f"\r\033[94m{bar}\033[0m",  # Blue progress bar
            f"\033[92m{percentage:5.1f}%\033[0m",  # Green percentage
            f"[{self.current:,}/{self.total:,}]"
        ]
        
        if self.show_speed and avg_speed > 0:
            status_parts.append(f"\033[96m{avg_speed:.1f} items/s\033[0m")  # Cyan speed
        
        status_parts.append(f"⏱ {elapsed_str}")
        
        if eta != "N/A":
            status_parts.append(f"ETA: {eta}")
        
        if message:
            status_parts.append(f"- {message}")
        
        status_line = " ".join(status_parts)
        
        # Print with proper clearing
        print(status_line + " " * 10, end='', flush=True)
        
        # New line when complete
        if self.current >= self.total:
            print()
    
    def finish(self, message: str = "Complete"):
        """Mark progress as complete"""
        self.current = self.total
        self._display(message)
        print()
        
        # Print summary
        total_time = time.time() - self.start_time
        avg_speed = self.total / total_time if total_time > 0 else 0
        
        print(f"\n\033[92m✓ {self.task_name} Complete!\033[0m")
        print(f"  Total Time: {str(timedelta(seconds=int(total_time)))}")
        print(f"  Items Processed: {self.total:,}")
        print(f"  Average Speed: {avg_speed:.2f} items/s\n")


class BatchProgressReporter:
    """
    Progress reporter for batch operations with multiple stages
    """
    
    def __init__(self, batch_size: int, total_items: int, task_name: str = "Processing"):
        self.batch_size = batch_size
        self.total_items = total_items
        self.task_name = task_name
        
        self.total_batches = (total_items + batch_size - 1) // batch_size
        self.current_batch = 0
        self.items_processed = 0
        
        self.start_time = time.time()
        self.batch_start_time = self.start_time
    
    def next_batch(self, items_in_batch: int, message: str = ""):
        """Move to next batch"""
        self.current_batch += 1
        self.items_processed += items_in_batch
        
        current_time = time.time()
        batch_time = current_time - self.batch_start_time
        self.batch_start_time = current_time
        
        # Calculate progress
        percentage = (self.items_processed / self.total_items * 100) if self.total_items > 0 else 0
        
        # Calculate ETA
        elapsed = current_time - self.start_time
        if self.items_processed > 0:
            rate = self.items_processed / elapsed
            remaining = self.total_items - self.items_processed
            eta_seconds = remaining / rate if rate > 0 else 0
            eta = str(timedelta(seconds=int(eta_seconds)))
        else:
            eta = "N/A"
        
        # Print status
        status = (
            f"\r\033[94mBatch {self.current_batch}/{self.total_batches}\033[0m "
            f"\033[92m{percentage:5.1f}%\033[0m "
            f"[{self.items_processed:,}/{self.total_items:,} items] "
            f"⏱ Batch: {batch_time:.1f}s "
            f"ETA: {eta}"
        )
        
        if message:
            status += f" - {message}"
        
        print(status + " " * 10, end='', flush=True)
        
        if self.items_processed >= self.total_items:
            print()
    
    def finish(self):
        """Complete batch processing"""
        total_time = time.time() - self.start_time
        print(f"\n\n\033[92m✓ {self.task_name} Complete!\033[0m")
        print(f"  Total Batches: {self.current_batch}")
        print(f"  Total Items: {self.items_processed:,}")
        print(f"  Total Time: {str(timedelta(seconds=int(total_time)))}")
        print(f"  Average: {self.items_processed/total_time:.2f} items/s\n")


# Example usage
if __name__ == "__main__":
    print("\n=== Testing ProgressReporter ===\n")
    
    # Test 1: Simple progress
    reporter = ProgressReporter(total=100, task_name="Test Task")
    for i in range(100):
        time.sleep(0.05)
        reporter.update(1, f"Item {i+1}")
    reporter.finish()
    
    time.sleep(1)
    
    # Test 2: Batch progress
    print("\n=== Testing BatchProgressReporter ===\n")
    batch_reporter = BatchProgressReporter(
        batch_size=25,
        total_items=100,
        task_name="Batch Processing"
    )
    
    for batch_num in range(4):
        time.sleep(0.5)
        batch_reporter.next_batch(25, f"Batch {batch_num + 1} complete")
    
    batch_reporter.finish()
