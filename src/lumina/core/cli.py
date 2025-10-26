"""
Command-line interface for Lumina
"""

import argparse
import os
import sys

from lumina.core.main import LuminaApp

def main():
    """Main entry point for the Lumina CLI"""
    parser = argparse.ArgumentParser(description="Lumina Smart Home Control System")
    subparsers = parser.add_subparsers(dest="command")

    # install command
    install_parser = subparsers.add_parser("install", help="Install Lumina systemd service")

    # run command
    run_parser = subparsers.add_parser("run", help="Run the Lumina application")
    run_parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    run_parser.add_argument("--no-web", action="store_true", help="Disable web interface")

    # status command
    status_parser = subparsers.add_parser("status", help="Get the status of the Lumina application")

    args = parser.parse_args()

    if args.command == "install":
        install_service()
    elif args.command == "run":
        run_app(args)
    elif args.command == "status":
        get_status()
    else:
        parser.print_help()

def run_app(args):
    """Run the Lumina application"""
    try:
        app = LuminaApp(debug=args.debug, enable_web=not args.no_web)
        success = app.run()

        if not success:
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⏹️  Application interrupted")
    except Exception as e:
        print(f"\n💥 Application failed: {e}")
        sys.exit(1)

def install_service():
    """Install the Lumina systemd service"""
    print("Installing Lumina systemd service...")
    service_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "lumina.service"))
    if not os.path.exists(service_file):
        print(f"Error: {service_file} not found.")
        return

    os.system(f"sudo cp {service_file} /etc/systemd/system/")
    os.system("sudo systemctl daemon-reload")
    os.system("sudo systemctl enable lumina.service")
    os.system("sudo systemctl start lumina.service")
    print("Lumina systemd service installed and started.")

def get_status():
    """Get the status of the Lumina systemd service"""
    os.system("sudo systemctl status lumina.service")

if __name__ == "__main__":
    main()
