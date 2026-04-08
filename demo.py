#!/usr/bin/env python3
"""
Traffic Violation Detection System - Demo Script

This script demonstrates how to run the traffic violation detection system.
"""

import os
import sys
import subprocess
import time

def print_header():
    """Print the system header."""
    print("=" * 60)
    print("🚗 TRAFFIC VIOLATION DETECTION SYSTEM 🚔")
    print("=" * 60)
    print()

def check_requirements():
    """Check if all requirements are met."""
    print("🔍 Checking requirements...")

    # Check if models directory exists
    if not os.path.exists('models'):
        os.makedirs('models')
        print("⚠️  Models directory created. Please download YOLOv8 model:")
        print("   wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt -O models/yolov8n.pt")
        print()

    # Check if evidence directory exists
    if not os.path.exists('evidence'):
        os.makedirs('evidence')
        print("📁 Evidence directory created")
        print()

    print("✅ Requirements check complete")
    print()

def run_edge_demo():
    """Run edge processing demo."""
    print("🎯 Starting Edge Processing Demo...")
    print("This will process a sample video (if available) or camera feed")
    print()

    # Check if sample video exists
    sample_video = "sample_traffic.mp4"
    if os.path.exists(sample_video):
        print(f"📹 Found sample video: {sample_video}")
        cmd = f"python edge/main.py --video {sample_video}"
    else:
        print("📹 No sample video found. Starting camera feed...")
        print("Press 'q' in the video window to quit")
        cmd = "python edge/main.py --live --display"

    try:
        print(f"Running: {cmd}")
        subprocess.run(cmd, shell=True)
    except KeyboardInterrupt:
        print("\n🛑 Edge processing stopped by user")

def run_cloud_api():
    """Run cloud API server."""
    print("☁️  Starting Cloud API Server...")
    print("API will be available at: http://localhost:8000")
    print("Press Ctrl+C to stop")
    print()

    try:
        subprocess.run("python cloud/main.py", shell=True)
    except KeyboardInterrupt:
        print("\n🛑 Cloud API stopped")

def run_dashboard():
    """Run web dashboard."""
    print("📊 Starting Web Dashboard...")
    print("Dashboard will be available at: http://localhost:5000")
    print("Press Ctrl+C to stop")
    print()

    try:
        subprocess.run("python dashboard/app.py", shell=True)
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped")

def show_menu():
    """Show the main menu."""
    print("Select an option:")
    print("1. 🧪 Run Tests")
    print("2. 🎯 Edge Processing Demo")
    print("3. ☁️  Start Cloud API")
    print("4. 📊 Start Dashboard")
    print("5. 🚀 Start All Services")
    print("6. 📚 Show Documentation")
    print("0. ❌ Exit")
    print()

def main():
    """Main function."""
    print_header()

    while True:
        show_menu()
        try:
            choice = input("Enter your choice (0-6): ").strip()

            if choice == "0":
                print("👋 Goodbye!")
                break
            elif choice == "1":
                print("🧪 Running tests...")
                os.system("python -m pytest tests/ -v")
                print()
            elif choice == "2":
                check_requirements()
                run_edge_demo()
            elif choice == "3":
                check_requirements()
                run_cloud_api()
            elif choice == "4":
                check_requirements()
                run_dashboard()
            elif choice == "5":
                print("🚀 Starting all services...")
                print("Note: This requires multiple terminal windows")
                print()
                print("Please run these commands in separate terminals:")
                print("1. Terminal 1: python cloud/main.py")
                print("2. Terminal 2: python dashboard/app.py")
                print("3. Terminal 3: python edge/main.py --live")
                print()
                input("Press Enter to continue...")
            elif choice == "6":
                print("📚 Documentation:")
                print("- README.md: Complete system documentation")
                print("- Workflow: Camera → Frame Extraction → YOLO → Tracking → Logic → OCR → Evidence → GPS → User ID → Cloud → E-Challan → Incentives → Dashboard")
                print("- Edge: Real-time processing on device")
                print("- Cloud: Centralized storage and analytics")
                print("- Dashboard: Web interface for monitoring")
                print()
                input("Press Enter to continue...")
            else:
                print("❌ Invalid choice. Please try again.")
                print()

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            print()

if __name__ == "__main__":
    main()