import click
import os
import sys
from .server import create_app

@click.group()
def cli():
    """Skuld - A web-based cron job scheduler with UI"""
    pass

@cli.command()
@click.option('--port', default=8000, help='Port to run the server on')
@click.option('--host', default='localhost', help='Host to run the server on')
def run(port, host):
    """Run the Skuld server"""
    app = create_app()
    click.echo(f"Starting Skuld server on http://{host}:{port}")
    app.run(host=host, port=port)

if __name__ == '__main__':
    cli() 