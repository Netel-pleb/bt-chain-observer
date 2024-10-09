def check_update_thread_status():
    try:
        with open('config/thread_status.status', 'r') as f:
            status = f.read().strip()
            return status
    except FileNotFoundError:
        return 'not running'