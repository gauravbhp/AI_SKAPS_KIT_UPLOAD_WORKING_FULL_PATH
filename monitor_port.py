import socket
import time
import os
import sys
from datetime import datetime, timedelta

class PortMonitor:
    def __init__(self, host="127.0.0.1", port=8000, interval=10, log_file="port_status.log"):
        self.host = host
        self.port = port
        self.interval = interval
        self.log_file = log_file
        self.start_time = None
        self.total_checks = 0
        self.successful_checks = 0
        self.failed_checks = 0
        self.last_status = None
        self.status_changed_at = None
        self.current_downtime_start = None
        
    def write_log(self, message):
        """Write message to log file with retry and fallback"""
        retry_count = 0
        log_path = self.log_file
        
        while retry_count < 3:
            try:
                with open(log_path, 'a') as f:
                    f.write(message + "\n")
                return True
            except PermissionError:
                retry_count += 1
                if retry_count >= 3:
                    os.makedirs('logs', exist_ok=True)
                    log_path = os.path.join('logs', os.path.basename(self.log_file))
                    try:
                        with open(log_path, 'a') as f:
                            f.write(message + "\n")
                        if not hasattr(self, '_fallback_notified'):
                            print(f"⚠ Note: Using {log_path} due to permission issues")
                            self._fallback_notified = True
                        return True
                    except Exception as e:
                        print(f"❌ Could not write to log: {e}")
                        return False
                time.sleep(0.1)
        return False
    
    def check_port(self):
        """Check if port is listening"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        
        try:
            result = sock.connect_ex((self.host, self.port))
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if result == 0:
                status = "SUCCESS"
                is_open = True
            else:
                status = "FAILURE"
                is_open = False
            
            message = f"[{timestamp}] {status}: Port {self.port} is {'LISTENING' if is_open else 'CLOSED'} on {self.host}"
            
            # Log to file only
            self.write_log(message)
            
            # Update statistics
            self.total_checks += 1
            if is_open:
                self.successful_checks += 1
            else:
                self.failed_checks += 1
            
            # Track status changes
            self._handle_status_change(is_open, timestamp)
            
            return is_open
            
        except socket.timeout:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message = f"[{timestamp}] TIMEOUT: Could not reach {self.host}:{self.port} (connection timed out)"
            print(f"⏱ {message}")
            self.write_log(message)
            self.total_checks += 1
            self.failed_checks += 1
            self._handle_status_change(False, timestamp)
            return False
            
        except Exception as e:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message = f"[{timestamp}] ERROR: Failed to check port {self.port} - {str(e)}"
            print(f"❌ {message}")
            self.write_log(message)
            self.total_checks += 1
            self.failed_checks += 1
            self._handle_status_change(False, timestamp)
            return False
        finally:
            sock.close()
    
    def _handle_status_change(self, is_open, timestamp):
        """Track and log status changes"""
        if self.last_status is not None and self.last_status != is_open:
            if is_open:
                # Port came back online
                downtime_duration = datetime.now() - self.current_downtime_start
                msg = f"[{timestamp}] ✓ PORT RECOVERED after {downtime_duration}"
                print(f"\n🟢 {msg}\n")
                self.write_log(msg)
            else:
                # Port went down
                self.current_downtime_start = datetime.now()
                msg = f"[{timestamp}] ✗ PORT DOWN - Service unreachable"
                print(f"\n🔴 {msg}\n")
                self.write_log(msg)
        elif self.last_status is None and not is_open:
            self.current_downtime_start = datetime.now()
        
        self.last_status = is_open
        self.status_changed_at = timestamp
    
    def get_stats(self):
        """Get monitoring statistics"""
        if self.total_checks == 0:
            return "No checks performed yet"
        
        uptime_pct = (self.successful_checks / self.total_checks) * 100
        elapsed = datetime.now() - self.start_time
        
        stats = f"""
╔═══════════════════════════════════════════════════════════╗
║           PORT MONITORING STATISTICS                      ║
╠═══════════════════════════════════════════════════════════╣
║ Target:              {self.host}:{self.port}
║ Monitoring Duration: {elapsed}
║ Total Checks:        {self.total_checks}
║ Successful:          {self.successful_checks} ✓
║ Failed:              {self.failed_checks} ✗
║ Uptime:              {uptime_pct:.1f}%
║ Last Status:         {'ONLINE' if self.last_status else 'OFFLINE'}
╚═══════════════════════════════════════════════════════════╝
        """
        return stats
    
    def run(self):
        """Start continuous monitoring"""
        self.start_time = datetime.now()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        print(f"""
╔════════════════════════════════════════════════════════════╗
║          PORT MONITORING STARTED                           ║
╠════════════════════════════════════════════════════════════╣
║ Host:     {self.host}
║ Port:     {self.port}
║ Interval: {self.interval}s
║ Log File: {self.log_file}
║ Started:  {timestamp}
║ 
║ Press Ctrl+C to stop and view statistics
╚════════════════════════════════════════════════════════════╝
        """)
        
        startup_msg = f"[{timestamp}] === Port Monitor Started === Target: {self.host}:{self.port} Interval: {self.interval}s"
        self.write_log(startup_msg)
        
        try:
            while True:
                self.check_port()
                time.sleep(self.interval)
        except KeyboardInterrupt:
            self._shutdown()
    
    def _shutdown(self):
        """Graceful shutdown with statistics"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        shutdown_msg = f"\n[{timestamp}] === Port Monitor Stopped ==="
        
        print(shutdown_msg)
        self.write_log(shutdown_msg)
        self.write_log(self.get_stats())
        
        print(self.get_stats())
        print("📊 Statistics saved to log file")


if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
    interval = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    log_file = sys.argv[4] if len(sys.argv) > 4 else "port_status.log"
    
    try:
        monitor = PortMonitor(host, port, interval, log_file)
        monitor.run()
    except ValueError as e:
        print(f"❌ Invalid arguments: {e}")
        print("Usage: python monitor_port_enhanced.py <host> <port> <interval> [log_file]")
        print("Example: python monitor_port_enhanced.py 192.168.3.48 5002 5")
        sys.exit(1)
