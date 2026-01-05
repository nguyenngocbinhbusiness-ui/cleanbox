
import pytest
import time
from unittest.mock import MagicMock, call
from shared.utils import retry, safe_execute

class TestUtils:
    def test_retry_success(self):
        """Test retry decorator on success."""
        mock_func = MagicMock(return_value="success")
        
        @retry(max_attempts=3, delay=0.01)
        def decorated_func():
            return mock_func()
            
        assert decorated_func() == "success"
        assert mock_func.call_count == 1

    def test_retry_failure_then_success(self):
        """Test retry failing once then succeeding."""
        mock_func = MagicMock(side_effect=[ValueError("fail"), "success"])
        
        @retry(max_attempts=3, delay=0.01, exceptions=(ValueError,))
        def decorated_func():
            return mock_func()
            
        assert decorated_func() == "success"
        assert mock_func.call_count == 2

    def test_retry_failure_max_attempts(self):
        """Test retry failing max attempts."""
        mock_func = MagicMock(side_effect=ValueError("fail"))
        
        @retry(max_attempts=3, delay=0.01, exceptions=(ValueError,))
        def decorated_func():
            return mock_func()
            
        with pytest.raises(ValueError):
            decorated_func()
        
        assert mock_func.call_count == 3

    def test_retry_on_retry_callback(self):
        """Test on_retry callback."""
        mock_callback = MagicMock()
        mock_func = MagicMock(side_effect=[ValueError("fail"), "success"])
        
        @retry(max_attempts=3, delay=0.01, on_retry=mock_callback)
        def decorated_func():
            return mock_func()
            
        decorated_func()
        assert mock_callback.call_count == 1
        # Check args: (exception, attempt)
        args = mock_callback.call_args[0]
        assert isinstance(args[0], ValueError)
        assert args[1] == 1

    def test_safe_execute_success(self):
        """Test safe_execute success."""
        func = lambda x: x + 1
        res = safe_execute(func, 1)
        assert res == 2

    def test_safe_execute_failure(self):
        """Test safe_execute failure returning default."""
        def func():
            raise ValueError("fail")
            
        res = safe_execute(func, default="default", log_error=True)
        assert res == "default"

    def test_safe_execute_no_log(self, caplog):
        """Test safe_execute failure without logging."""
        def func():
            raise ValueError("fail")
            
        safe_execute(func, log_error=False)
        assert "failed" not in caplog.text
