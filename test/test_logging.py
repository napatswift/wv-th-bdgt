import pytest
from loguru import logger

def simple_logging_function():
    logger.info("This is a test log message.")

def test_loguru_message_capture():
    log_capture_list = []

    # Define a sink function to append log messages to the list
    def list_sink(message):
        log_capture_list.append(message.record)

    # Add the list-based sink
    sink_id = logger.add(list_sink)

    # Call the function that logs a message
    simple_logging_function()

    # Remove the sink to stop capturing
    logger.remove(sink_id)

    # Assert that the log message was captured
    assert len(log_capture_list) == 1
    log_record = log_capture_list[0]
    assert log_record["level"].name == "INFO"
    assert log_record["message"] == "This is a test log message."
