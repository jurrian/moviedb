import json
import logging
import os
from enum import Enum

import sentry_sdk
import streamlit as st
from streamlit.components.v1 import html


class StreamlitWriteHandler(logging.Handler):
    def emit(self, record):
        log_entry = self.format(record)
        if record.levelno == logging.WARNING:
            st.warning(log_entry)
            console(log_entry, severity=Severity.WARN)
        elif record.levelno == logging.ERROR:
            st.error(log_entry)
            console(log_entry, severity=Severity.ERROR)
        else:
            st.write(log_entry)
            console(log_entry)


@st.cache_data(show_spinner=False)
def setup_logging():
    # Configure the logging
    logging.root.handlers.clear()
    logging.basicConfig(level=logging.WARNING, format='[%(asctime)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    logger = logging.getLogger('app')
    logger.setLevel(logging.INFO)
    logger.addHandler(StreamlitWriteHandler())
    return logger


@st.cache_data(show_spinner=False)
def sentry_patch_streamlit():
    """Streamlit catches all exceptions, this monkey patch send exceptions to Sentry.
    """
    import sys
    script_runner = sys.modules["streamlit.runtime.scriptrunner.exec_code"]
    original_func = script_runner.handle_uncaught_app_exception

    def sentry_patched_func(ex):
        sentry_sdk.capture_exception(ex)
        original_func(ex)

    script_runner.handle_uncaught_app_exception = sentry_patched_func


@st.cache_data(show_spinner=False)
def setup_sentry():
    # Only enable Sentry for live environments, not for local development
    if os.getenv('SENTRY_SDK'):
        sentry_sdk.init(
            environment=os.getenv('SENTRY_SDK'),
            send_default_pii=True,
            traces_sample_rate=0.1,
            _experiments={
                # Set continuous_profiling_auto_start to True to automatically start the profiler on when possible.
                "continuous_profiling_auto_start": True,
            },
        )
        sentry_patch_streamlit()


class Severity(Enum):
    LOG = "log"
    WARN = "warn"
    ERROR = "error"


def console(message: str, severity: Severity = Severity.LOG):
    html(f"""
    <script>
        console.{severity.value}({json.dumps(message)});
    </script>
    """)
