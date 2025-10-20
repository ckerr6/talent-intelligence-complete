#!/usr/bin/env python3
# ABOUTME: Script to run the FastAPI server
# ABOUTME: Provides development and production modes

import argparse
import uvicorn
from api.config import settings


def main():
    """Run the FastAPI server"""
    parser = argparse.ArgumentParser(description='Run Talent Intelligence API server')
    parser.add_argument(
        '--host',
        default=settings.HOST,
        help=f'Host to bind to (default: {settings.HOST})'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=settings.PORT,
        help=f'Port to bind to (default: {settings.PORT})'
    )
    parser.add_argument(
        '--reload',
        action='store_true',
        default=settings.RELOAD,
        help='Enable auto-reload (development mode)'
    )
    parser.add_argument(
        '--no-reload',
        action='store_true',
        help='Disable auto-reload (production mode)'
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=1,
        help='Number of worker processes (production mode)'
    )
    
    args = parser.parse_args()
    
    # Determine reload setting
    reload = args.reload and not args.no_reload
    
    print("="*80)
    print("🚀 Starting Talent Intelligence API")
    print("="*80)
    print(f"Host: {args.host}")
    print(f"Port: {args.port}")
    print(f"Mode: {'Development (auto-reload)' if reload else 'Production'}")
    print(f"Workers: {args.workers}")
    print("="*80)
    print(f"\n📍 API will be available at: http://{args.host}:{args.port}")
    print(f"📚 Documentation at: http://{args.host}:{args.port}/docs")
    print(f"📋 ReDoc at: http://{args.host}:{args.port}/redoc\n")
    
    # Run server
    uvicorn.run(
        "api.main:app",
        host=args.host,
        port=args.port,
        reload=reload,
        workers=args.workers if not reload else 1,
        log_level="info"
    )


if __name__ == "__main__":
    main()

