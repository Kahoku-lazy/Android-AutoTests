"""
AgentScope 2.0 FastAPI service launcher.
Start separately from the Django server — this runs on port 8000 by default.

Usage:
    python run_agentscope.py                  # start (blocking)
    python run_agentscope.py --port 8001      # custom port
"""
import os
import sys
import argparse


def main():
    parser = argparse.ArgumentParser(description='AgentScope 2.0 Agent Service')
    parser.add_argument('--host', default='0.0.0.0', help='Bind host (default 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8000, help='Bind port (default 8000)')
    parser.add_argument('--reload', action='store_true', help='Enable auto-reload (dev only)')
    args = parser.parse_args()

    # Ensure Django settings module is set before any Django imports
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

    import django
    django.setup()

    import uvicorn
    from agentscope_service.app import create_agentscope_app
    from config.agentscope_config import TITLE, VERSION

    app = create_agentscope_app()

    print(f'  {TITLE} v{VERSION}')
    print(f'  Starting at http://{args.host}:{args.port}')
    print(f'  API docs at http://{args.host}:{args.port}/docs')

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level='info',
    )


if __name__ == '__main__':
    main()
