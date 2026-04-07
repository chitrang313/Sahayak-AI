"""Application entry point for the Sahayak AI desktop app."""

from ui.layout import SahayakAIApp


def main() -> None:
    """Create and run the desktop application."""
    app = SahayakAIApp()
    app.run()


if __name__ == "__main__":
    main()
