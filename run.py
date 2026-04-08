#!/usr/bin/env python3
"""
Traffic Violation Detection System - Main Runner

This script provides commands to run different parts of the system:
- edge: Run edge processing
- cloud: Run cloud API server
- dashboard: Run web dashboard
- all: Run all services
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path

def run_edge(args):
    """Run edge processing."""
    print("Starting Edge Processing...")
    os.chdir('edge')
    cmd = [sys.executable, 'main.py']
    if args.video:
        cmd.extend(['--video', args.video])
    if args.live:
        cmd.append('--live')
    if args.user_id:
        cmd.extend(['--user-id', args.user_id])
    if args.display:
        cmd.append('--display')

    subprocess.run(cmd)

def run_cloud(args):
    """Run cloud API server."""
    print("Starting Cloud API Server...")
    os.chdir('cloud')
    cmd = [sys.executable, 'main.py']
    subprocess.run(cmd)

def run_dashboard(args):
    """Run web dashboard."""
    print("Starting Dashboard...")
    os.chdir('dashboard')
    cmd = [sys.executable, 'app.py']
    subprocess.run(cmd)

def run_all(args):
    """Run all services (requires multiple terminals)."""
    print("Starting all services...")
    print("Note: This requires multiple terminal windows.")
    print("Please run each service in separate terminals:")
    print()
    print("Terminal 1 - Cloud API:")
    print("  cd cloud && python main.py")
    print()
    print("Terminal 2 - Dashboard:")
    print("  cd dashboard && python app.py")
    print()
    print("Terminal 3 - Edge Processing:")
    print("  cd edge && python main.py --live")
    print()
    print("Or use individual commands: python run.py edge --live")

def install_dependencies():
    """Install required dependencies."""
    print("Installing dependencies...")
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])

def setup_models():
    """Download and setup models."""
    print("Setting up models...")
    models_dir = Path('models')
    models_dir.mkdir(exist_ok=True)

    # Download YOLOv8 model (you would implement actual download)
    print("Please download YOLOv8 model to models/yolov8n.pt")
    print("You can get it from: https://github.com/ultralytics/ultralytics")

def main():
    parser = argparse.ArgumentParser(description='Traffic Violation Detection System')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Edge parser
    edge_parser = subparsers.add_parser('edge', help='Run edge processing')
    edge_parser.add_argument('--video', type=str, help='Path to video file')
    edge_parser.add_argument('--live', action='store_true', help='Process live feed')
    edge_parser.add_argument('--user-id', type=str, help='User ID for citizen reports')
    edge_parser.add_argument('--display', action='store_true', help='Display video feed')
    edge_parser.set_defaults(func=run_edge)

    # Cloud parser
    cloud_parser = subparsers.add_parser('cloud', help='Run cloud API server')
    cloud_parser.set_defaults(func=run_cloud)

    # Dashboard parser
    dashboard_parser = subparsers.add_parser('dashboard', help='Run web dashboard')
    dashboard_parser.set_defaults(func=run_dashboard)

    # All parser
    all_parser = subparsers.add_parser('all', help='Run all services (instructions)')
    all_parser.set_defaults(func=run_all)

    # Setup parser
    setup_parser = subparsers.add_parser('setup', help='Setup the system')
    setup_parser.set_defaults(func=lambda x: (install_dependencies(), setup_models()))

    args = parser.parse_args()

    if args.command:
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()