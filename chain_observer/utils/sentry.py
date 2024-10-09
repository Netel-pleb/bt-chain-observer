from dotenv import load_dotenv
import os
import sentry_sdk
import logging
from sentry_sdk.integrations.logging import LoggingIntegration



logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def init_sentry():
    """Initialize Sentry for error tracking."""
    load_dotenv()
    
    sentry_logging = LoggingIntegration(
    level=logging.INFO,        # Capture info and above as breadcrumbs
    event_level=logging.ERROR  # Send errors as events
    
    )

    sentry_dsn = os.getenv('SENTRY_DSN')
    
    if sentry_dsn:
        sentry_sdk.init(
            dsn=sentry_dsn,
            traces_sample_rate=1.0,
            integrations=[sentry_logging]
        )
        logging.info("Sentry initialized successfully.")
    else:
        logging.warning("SENTRY_DSN not found. Sentry initialization skipped.")
