import socket
import time
import os
import sys
from datetime import datetime

def check_port(host, port, log_file="port_status.log"):
    """Check if port is listening and log the result"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    
    try:
        result = sock.connect_ex((host, port))
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if result == 0:
            status = "SUCCESS"
            message = f"[{timestamp}] {status}: Port {port} is LISTENING on {host}"
        else:
            status = "FAILURE"
            message = f"[{timestamp}] {status}: Port {port} is CLOSED on {host}"
        
        # Write to log file only (no console print)
        write_log(message, log_file)
        
        return result == 0
        
    except socket.timeout:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"[{timestamp}] TIMEOUT: Could not reach {host}:{port} (connection timed out)"
        write_log(message, log_file)
        return False
        
    except Exception as e:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"[{timestamp}] ERROR: Failed to check port {port} - {str(e)}"
        write_log(message, log_file)
        return False
    finally:
        sock.close()


def write_log(message, log_file="port_status.log"):
    """Write message to log file with retry and fallback"""
    retry_count = 0
    log_path = log_file
    
    while retry_count < 3:
        try:
            with open(log_path, 'a') as f:
                f.write(message + "\n")
            return True
        except PermissionError:
            retry_count += 1
            if retry_count >= 3:
                os.makedirs('logs', exist_ok=True)
                log_path = os.path.join('logs', os.path.basename(log_file))
                try:
                    with open(log_path, 'a') as f:
                        f.write(message + "\n")
                    return True
                except Exception:
                    return False
            time.sleep(0.1)
    return False


def monitor_port(host="127.0.0.1", port=8000, interval=10, log_file="port_status.log"):
    """Continuously monitor port and log status"""
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    startup_msg = f"\n[{timestamp}] === Port Monitor Started === Target: {host}:{port} Interval: {interval}s"
    write_log(startup_msg, log_file)
    
    print(f"Starting continuous port monitoring on {host}:{port}")
    print(f"Check interval: {interval}s")
    print(f"Log file: {log_file}")
    print("All output will be written to log file. Press Ctrl+C to stop.\n")
    
    try:
        while True:
            check_port(host, port, log_file)
            time.sleep(interval)
    except KeyboardInterrupt:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        shutdown_msg = f"[{timestamp}] === Port Monitor Stopped ==="
        write_log(shutdown_msg, log_file)
        print("\n✓ Monitoring stopped. Results written to log file.")


if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8000
    interval = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    log_file = sys.argv[4] if len(sys.argv) > 4 else "port_status.log"
    
    try:
        monitor_port(host, port, interval, log_file)
    except ValueError as e:
        print(f"❌ Invalid arguments: {e}")
        print("Usage: python monitor_port.py <host> <port> <interval> [log_file]")
        print("Example: python monitor_port.py 192.168.3.48 5002 5")
        sys.exit(1)
