# Background File Monitor Setup - Summary

## Changes Made

### 1. **Added APScheduler to Requirements** 
- Updated `requirements.txt` to include `apscheduler==3.10.4`
- Installed the package successfully

### 2. **Updated App Configuration** (`packing_system/apps.py`)
- Modified `PackingSystemConfig` to initialize the background scheduler when Django starts
- The `ready()` method now calls `start_file_monitor()` on app startup

### 3. **Created Background Scheduler** (`packing_system/scheduler.py`)
- New file that handles all scheduling logic
- Main functions:
  - `check_and_process_txt_files()` - Checks for .txt files and processes them
  - `start_file_monitor()` - Starts the background scheduler (runs every 5 minutes by default)
  - `stop_file_monitor()` - Stops the scheduler if needed
  - `get_scheduler_status()` - Returns current scheduler status

### 4. **Updated Views** (`packing_system/views.py`)
- Removed the module-level `everytime_check()` call that only ran once
- Added three new API endpoints for scheduler management:
  - `scheduler_status` - GET endpoint to check scheduler status
  - `trigger_file_check_now` - POST endpoint to manually trigger file check
  - `update_check_interval` - POST endpoint to change check interval

### 5. **Added URL Routes** (`packing_system/urls.py`)
- Added three new URL patterns for scheduler management:
  - `/api/scheduler/status/` - Check scheduler status
  - `/api/scheduler/trigger-check/` - Manually trigger file check
  - `/api/scheduler/update-interval/` - Update check interval

## How It Works

1. **On Django Startup**: 
   - The scheduler automatically starts and is configured to check for txt files every 5 minutes

2. **Background Check**:
   - Every 5 minutes, the scheduler calls `check_and_process_txt_files()`
   - If txt files are found in SOURCE_DIR, it automatically calls `move_txt_files()`
   - Logging is performed for each check

3. **Manual Control**:
   - You can trigger an immediate check via API: `POST /api/scheduler/trigger-check/`
   - You can change the interval: `POST /api/scheduler/update-interval/` with `interval` parameter (in minutes)
   - You can check status: `GET /api/scheduler/status/`

## Default Configuration

- **Check Interval**: 5 minutes (configurable via API)
- **Behavior**: Runs continuously when Django is running
- **Logging**: All checks are logged with [FILE_MONITOR] prefix

## API Endpoints

### 1. Get Scheduler Status
```
GET /packing_system/api/scheduler/status/
Response: {
    "status": "success",
    "scheduler": {
        "running": true,
        "jobs": 1,
        "jobs_list": [...]
    }
}
```

### 2. Manually Trigger File Check
```
POST /packing_system/api/scheduler/trigger-check/
Response: {
    "status": "success",
    "message": "File check triggered successfully"
}
```

### 3. Update Check Interval
```
POST /packing_system/api/scheduler/update-interval/
Parameters: interval=10  (in minutes)
Response: {
    "status": "success",
    "message": "Check interval updated to 10 minute(s)",
    "new_interval": 10
}
```

## No More Manual Running Needed

Before: `everytime_check()` was only called once when the module loaded  
Now: The function runs automatically every 5 minutes in the background while Django is running

The scheduler will continue checking for txt files in `SOURCE_DIR` and processing them automatically without any manual intervention needed.
