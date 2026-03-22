from unittest.mock import patch

import pytest

from ui.views.storage_view_actions import ProtectedPathError, open_file_location, recycle_path


class TestStorageViewActions:
    def test_recycle_path_rejects_protected_targets(self):
        with patch("ui.views.storage_view_actions.is_protected_path", return_value=True):
            with pytest.raises(ProtectedPathError):
                recycle_path("C:\\Windows")

    def test_recycle_path_raises_for_missing_target(self):
        with patch("ui.views.storage_view_actions.is_protected_path", return_value=False):
            with pytest.raises(FileNotFoundError):
                recycle_path("C:\\missing.txt")

    def test_recycle_path_calls_winshell(self, tmp_path):
        target = tmp_path / "demo.txt"
        target.write_text("x")

        with patch("ui.views.storage_view_actions.winshell.delete_file") as delete_mock:
            recycle_path(str(target))

        delete_mock.assert_called_once()

    def test_open_file_location_uses_explorer_select(self, tmp_path):
        target = tmp_path / "demo.txt"
        target.write_text("x")

        with patch("ui.views.storage_view_actions.subprocess.run") as run_mock:
            open_file_location(str(target))

        run_mock.assert_called_once()
        assert run_mock.call_args[0][0][0] == "explorer"
        assert run_mock.call_args[0][0][1] == "/select,"

    def test_open_file_location_raises_for_missing_target(self):
        with pytest.raises(FileNotFoundError):
            open_file_location("C:\\missing.txt")
