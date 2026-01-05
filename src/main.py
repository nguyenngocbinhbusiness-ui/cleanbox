"""CleanBox - Main entry point."""
from shared.constants import APP_NAME, CONFIG_DIR
import logging
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))


def setup_logging() -> None:
    """Set up logging configuration."""
    try:
        log_file = CONFIG_DIR / "cleanbox.log"
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_file, encoding="utf-8"),
                logging.StreamHandler(),
            ],
        )
    except Exception as e:
        print(f"Failed to setup logging: {e}")
        # Fallback to basic logging to stderr
        logging.basicConfig(level=logging.INFO, stream=sys.stderr)


def main() -> int:
    """Main entry point."""
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        logger.info("=" * 50)
        logger.info("Starting %s", APP_NAME)
        logger.info("=" * 50)

        from app import App
        app = App()
        return app.start()

    except Exception as e:
        logger.exception("Fatal error: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
