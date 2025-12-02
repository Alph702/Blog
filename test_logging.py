#!/usr/bin/env python3
"""Quick test to verify logging is working"""

import logging
from utils.logger import setup_logging

# Setup logging
main_logger = setup_logging(log_file="test.log", level=logging.DEBUG)

# Test different loggers
main_logger.info("✓ Main logger test")
main_logger.debug("✓ Main logger debug")

# Test module logger
module_logger = logging.getLogger("test_module")
module_logger.info("✓ Module logger test")
module_logger.debug("✓ Module logger debug")

# Test nested module logger
nested_logger = logging.getLogger("test_module.sub")
nested_logger.info("✓ Nested module logger test")
nested_logger.debug("✓ Nested module logger debug")

print("\n✓ Logging test complete. Check logs/test.log")
