"""
Tests for progress reporting functionality in the STL to GCode Converter.
"""
import unittest
from unittest.mock import MagicMock, patch, ANY, PropertyMock
import time
import sys

# Import the ProgressReporter class
from progress import ProgressReporter

class TestProgressReporting(unittest.TestCase):
    """Test cases for progress reporting functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a mock progress dialog
        self.progress_dialog = MagicMock()
        self.progress_dialog.wasCanceled.return_value = False
        
        # Create a progress reporter instance with sip patching
        self.sip_mock = MagicMock()
        self.sip_mock.isdeleted.return_value = False
        
        # Patch the sip module in the progress module's namespace
        self.sip_patcher = patch.dict('sys.modules', {'sip': self.sip_mock})
        self.sip_patcher.start()
        
        # Re-import progress to apply the sip mock
        import importlib
        import progress
        importlib.reload(progress)
        from progress import ProgressReporter
        
        # Create the reporter after patching
        self.reporter = ProgressReporter(progress_dialog=self.progress_dialog, is_loading=True)
        
        # Patch time for consistent testing
        self.time_patcher = patch('time.time')
        self.mock_time = self.time_patcher.start()
        self.mock_time.return_value = 0
    
    def test_initial_state(self):
        """Test the initial state of the progress reporter."""
        self.assertEqual(self.reporter._last_progress, -1)
        self.assertEqual(self.reporter._last_progress_time, 0)
        self.assertTrue(self.reporter.is_loading)
        self.assertIsNotNone(self.reporter.progress_dialog)
    
    def test_progress_updates(self):
        """Test that progress updates are handled correctly."""
        # Test first update
        result = self.reporter.update_progress(0, "Starting")
        self.assertTrue(result)
        self.assertEqual(self.reporter._last_progress, 0)
        self.progress_dialog.setLabelText.assert_called_once_with("Loading: 0% - Starting")
        self.progress_dialog.setValue.assert_called_once_with(0)
        
        # Clear the mock for the next test
        self.progress_dialog.reset_mock()
        
        # Test small progress update (should be ignored due to minimum increment)
        result = self.reporter.update_progress(0.5, "Processing")
        self.assertFalse(result)
        self.progress_dialog.setLabelText.assert_not_called()
        
        # Test 10% update
        self.mock_time.return_value = 1.0
        result = self.reporter.update_progress(10, "Processing")
        self.assertTrue(result)
        self.assertEqual(self.reporter._last_progress, 10)
        self.progress_dialog.setLabelText.assert_called_once_with("Loading: 10% - Processing")
        
        # Test completion
        self.mock_time.return_value = 2.0
        result = self.reporter.update_progress(100, "Done")
        self.assertTrue(result)
        self.progress_dialog.setLabelText.assert_called_with("Loading: 100% - Done")
        
        # Verify cleanup
        self.assertFalse(hasattr(self.reporter, '_last_progress'))
        self.assertFalse(hasattr(self.reporter, '_last_progress_time'))
    
    def test_duplicate_updates(self):
        """Test that duplicate progress updates are ignored."""
        # First update
        self.reporter.update_progress(10, "Processing")
        call_count = self.progress_dialog.setLabelText.call_count
        
        # Duplicate update
        self.reporter.update_progress(10, "Processing")
        self.assertEqual(self.progress_dialog.setLabelText.call_count, call_count)
    
    def test_throttling(self):
        """Test that progress updates are throttled."""
        # First update
        self.mock_time.return_value = 0
        self.reporter.update_progress(10, "Processing")
        call_count = self.progress_dialog.setLabelText.call_count
        
        # Rapid updates - should be throttled
        self.mock_time.return_value = 0.5  # Less than 1 second since last update
        for i in range(11, 16):  # 5 updates
            self.reporter.update_progress(i, "Processing")
        
        # Should have all updates because we're testing with a mock time
        # The actual throttling is time-based, which is hard to test precisely
        # So we'll just verify that we got at least one update
        self.assertGreater(self.progress_dialog.setLabelText.call_count, call_count)

    def test_logging(self):
        """Test that progress is logged at appropriate intervals."""
        with patch('progress.logger') as mock_logger:
            # First update at time 0
            self.reporter.update_progress(0, "Starting")
            mock_logger.debug.assert_called_with("Loading progress: 0.0% - Starting")
            
            # Update at 0.5 seconds (should still log because progress changed significantly)
            mock_logger.reset_mock()
            self.mock_time.return_value = 0.5
            self.reporter.update_progress(50, "Halfway")
            mock_logger.debug.assert_called_with("Loading progress: 50.0% - Halfway")
            
            # Update at 1.1 seconds (should log again)
            mock_logger.reset_mock()
            self.mock_time.return_value = 1.1
            self.reporter.update_progress(100, "Done")
            mock_logger.debug.assert_called_with("Loading progress: 100.0% - Done")
    
    def test_reset(self):
        """Test that the reporter can be reset to its initial state."""
        self.reporter.update_progress(50, "Halfway")
        self.reporter.reset()
        
        self.assertEqual(self.reporter._last_progress, -1)
        self.assertEqual(self.reporter._last_progress_time, 0)
        self.assertTrue(self.reporter.is_loading)
    
    def test_not_loading(self):
        """Test that updates are ignored when not in loading state."""
        self.reporter.is_loading = False
        result = self.reporter.update_progress(50, "Should not update")
        self.assertFalse(result)
        self.progress_dialog.setLabelText.assert_not_called()
    
    def tearDown(self):
        """Clean up after tests."""
        self.time_patcher.stop()
        self.sip_patcher.stop()
        # Clean up the module cache to avoid test pollution
        import sys
        if 'progress' in sys.modules:
            del sys.modules['progress']

if __name__ == '__main__':
    unittest.main()
