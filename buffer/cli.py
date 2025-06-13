import click
from flask import Flask
from .server import create_app

@click.group()
def cli():
    """Buffer - A message buffer platform with web interface"""
    pass

@cli.command()
@click.option('--host', default='127.0.0.1', help='Host to bind the server to')
@click.option('--port', default=5000, help='Port to bind the server to')
def run(host, port):
    """Run the Buffer server"""
    app = create_app()
    click.echo(f"Starting Buffer server on http://{host}:{port}")
    app.run(host=host, port=port, debug=True)

if __name__ == '__main__':
    cli() 