from core.logging import configure_logging
from .main import cli_app 

#Script entry point (path independent)
if __name__ == "__main__":
    configure_logging()
    #Start Typer CLI application
    cli_app()
