
import sys
import unittest
from PyQt6.QtWidgets import QApplication

# Ensure src is in path
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from ui.main_window import MainWindow
from ui.components.sidebar import SidebarWidget

class TestUIStructure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create QApplication instance if it doesn't exist
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def test_sidebar_creation(self):
        sidebar = SidebarWidget()
        self.assertIsNotNone(sidebar)
        # Check if items can be added
        sidebar.add_item("Test", "test_id")
        self.assertIn("test_id", sidebar.buttons)

    def test_mainwindow_creation(self):
        window = MainWindow()
        self.assertIsNotNone(window)
        
        # Check structure
        self.assertIsInstance(window.sidebar, SidebarWidget)
        self.assertIsNotNone(window.splitter)
        self.assertIsNotNone(window.content_stack)
        
        # Check default view count (Drives, Cleanup, Settings)
        self.assertEqual(window.content_stack.count(), 3)

if __name__ == '__main__':
    unittest.main()
