from pathlib import Path

from tests.ten_testcases import TenTestCase
import unittest
import tempfile


from tenlib import flow, logging


class TestLogging(TenTestCase):
    def setUp(self) -> None:
        super().setUp()
        logging.set_file(None)
        logging.set_cli_level(None)

    def tearDown(self) -> flow.NoneType:
        logging.set_file(None)
        logging.set_cli_level(None)
        super().tearDown()

    def test_cli_logging_while_displaying_data_works(self):
        def display_both():
            logging.set_cli_level(logging.DEBUG)
            flow.msg_info("test")
            logging.log.debug("This is a debug message")

        output = self._read_output(display_both)
        self.assertIn("test\n", output)
        self.assertIn("This is a debug message", output)

    def test_change_log_file(self):
        with tempfile.TemporaryDirectory() as tempdir:
            log_path = Path(tempdir) / "test.log"
            logging.set_file(str(log_path))
            logging.set_level("DEBUG")
            logging.log.debug("This is a debug message")
            data = log_path.read_text()
            self.assertIn("This is a debug message", data)

    def test_change_log_file_twice(self):
        with tempfile.TemporaryDirectory() as tempdir:
            # First file
            log_path = Path(tempdir) / "test.log"
            logging.set_file(str(log_path))
            logging.set_level("DEBUG")
            logging.log.debug("This is a debug message")
            data = log_path.read_text()
            self.assertIn("This is a debug message", data)

            # Second file
            log_path = Path(tempdir) / "test2.log"
            logging.set_file(str(log_path))
            logging.set_level("DEBUG")
            logging.log.debug("This is a second debug message")
            data = log_path.read_text()
            self.assertIn("This is a second debug message", data)

    def test_change_cli_log_level(self):
        def display_first_and_third():
            logging.set_cli_level("INFO")
            logging.log.info("This is an info message")
            logging.log.debug("This is a debug message (not displayed)")
            logging.set_cli_level("DEBUG")
            logging.log.debug("This is a debug message (displayed)")

        output = self._read_output(display_first_and_third)
        self.assertIn("This is an info message", output)
        self.assertIn("This is a debug message (displayed)", output)

    def test_set_file_level_before_set_file_works(self):
        logging.set_level("DEBUG")
        logging.log.debug("This is a debug message")

    def test_handlers_with_distinct_log_levels(self):
        log_data = ""

        def test_both() -> flow.NoneType:
            nonlocal log_data
            with tempfile.TemporaryDirectory() as tempdir:
                log_path = Path(tempdir) / "test.log"
                logging.set_file(str(log_path))
                logging.set_level("INFO")
                logging.set_cli_level("DEBUG")
                logging.log.info("This lands in both CLI and file")
                logging.log.debug("This lands only in CLI")
                log_data = log_path.read_text()

        cli_data = self._read_output(test_both)

        self.assertNotIn("This lands only in CLI", log_data)
        self.assertIn("This lands in both CLI and file", log_data)
        self.assertIn("This lands only in CLI", cli_data)
        self.assertIn("This lands in both CLI and file", cli_data)

    def test_cli_logging_can_get_disabled_and_reenabled(self):
        def display_both():
            logging.set_cli_level(logging.DEBUG)
            self._check_only_has_cli_logger(enabled=True)
            logging.log.debug("This is displayed")
            logging.set_cli_level(None)
            self._check_only_has_cli_logger(enabled=False)
            logging.log.debug("This is not displayed")
            logging.set_cli_level(logging.DEBUG)
            self._check_only_has_cli_logger(enabled=True)
            logging.log.debug("This is also displayed")

        output = self._read_output(display_both)
        self.assertIn("This is displayed", output)
        self.assertNotIn("This is not displayed", output)
        self.assertIn("This is also displayed", output)

    def _check_only_has_cli_logger(self, enabled: bool = False):
        self.assertEqual(len(logging._get_root_logger().handlers), 1)
        self.assertIsInstance(
            logging._get_root_logger().handlers[0], logging.CLIHandler
        )
        self.assertIs(logging._get_root_logger().handlers[0].enabled, enabled)

    def test_cli_logging_can_get_disabled_twice(self):
        logging.set_cli_level(None)
        self._check_only_has_cli_logger()
        logging.set_cli_level(None)
        self._check_only_has_cli_logger()

    def test_trace_logging_is_not_greater_than_debug(self):
        self.assertGreater(logging.DEBUG, logging.TRACE)

    def test_file_logging_can_get_disabled_twice_through_set_level(self):
        logging.set_level(None)
        self._check_only_has_cli_logger()
        logging.set_level(None)
        self._check_only_has_cli_logger()

    def test_file_logging_can_get_disabled_twice_through_set_file(self):
        logging.set_file(None)
        self._check_only_has_cli_logger()
        logging.set_file(None)
        self._check_only_has_cli_logger()

    def test_log_object_is_of_type_TenLogger(self):
        self.assertIsInstance(logging.log, logging.TenLogger)

    def test_logger_object_is_of_type_TenLogger(self):
        self.assertIsInstance(logging.logger("test"), logging.TenLogger)


if __name__ == "__main__":
    unittest.main()
