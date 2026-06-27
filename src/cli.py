#!/usr/bin/env python3
"""
CLI interface for Telegram Calendar Bot

Provides commands to manage the bot: start, stop, status, config, setup
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import signal
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, Optional

import psutil
from dotenv import load_dotenv

from .telegram_bot import create_telegram_bot


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BotManager:
    """Manages bot lifecycle and configuration."""
    
    def __init__(self, config_dir: str = "."):
        self.config_dir = Path(config_dir)
        self.pid_file = self.config_dir / "bot.pid"
        self.log_file = self.config_dir / "bot.log"
        self.config_file = self.config_dir / "config.json"
        self.env_file = self.config_dir / ".env"
        
    def start(self, daemon: bool = False) -> None:
        """Start the Telegram bot."""
        # Check if already running
        if self.is_running():
            pid = self.get_pid()
            print(f"❌ Bot is already running (PID: {pid})")
            return
            
        # Load configuration
        if not self.env_file.exists():
            print(f"❌ Environment file not found: {self.env_file}")
            print("Run 'bot setup' to create configuration")
            return
            
        load_dotenv(self.env_file)
        
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not token:
            print("❌ TELEGRAM_BOT_TOKEN not found in environment")
            return
            
        print("🚀 Starting Telegram Calendar Bot...")
        
        if daemon:
            self._start_daemon()
        else:
            self._start_foreground()
    
    def stop(self) -> None:
        """Stop the Telegram bot."""
        if not self.is_running():
            print("❌ Bot is not running")
            return
            
        pid = self.get_pid()
        try:
            os.kill(pid, signal.SIGTERM)
            
            # Wait for graceful shutdown
            for _ in range(10):
                if not self.is_running():
                    break
                time.sleep(1)
            else:
                # Force kill if still running
                try:
                    os.kill(pid, signal.SIGKILL)
                    print("⚠️ Bot forcefully terminated")
                except ProcessLookupError:
                    pass
                    
            self.pid_file.unlink(missing_ok=True)
            print("✅ Bot stopped")
            
        except ProcessLookupError:
            print("❌ Bot process not found")
            self.pid_file.unlink(missing_ok=True)
        except PermissionError:
            print("❌ Permission denied. Try running as administrator")
    
    def status(self) -> None:
        """Show bot status and statistics."""
        print("📊 Telegram Calendar Bot Status")
        print("=" * 40)
        
        if self.is_running():
            pid = self.get_pid()
            try:
                process = psutil.Process(pid)
                cpu_percent = process.cpu_percent(interval=1)
                memory_info = process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024
                
                print(f"🟢 Status: Running")
                print(f"🔢 PID: {pid}")
                print(f"📈 CPU: {cpu_percent:.1f}%")
                print(f"💾 Memory: {memory_mb:.1f} MB")
                print(f"⏰ Started: {time.ctime(process.create_time())}")
                
                # Show log tail if available
                if self.log_file.exists():
                    print(f"📝 Log file: {self.log_file}")
                    print("\n📋 Recent logs:")
                    self._show_log_tail()
                    
            except psutil.NoSuchProcess:
                print("🔴 Status: Dead (PID file exists but process not found)")
                self.pid_file.unlink(missing_ok=True)
        else:
            print("🔴 Status: Stopped")
            
        # Show configuration
        print(f"\n⚙️ Configuration:")
        if self.env_file.exists():
            load_dotenv(self.env_file)
            token = os.getenv('TELEGRAM_BOT_TOKEN', 'Not set')
            masked_token = token[:8] + '...' + token[-8:] if len(token) > 16 else 'Not set'
            print(f"🔑 Bot Token: {masked_token}")
            print(f"📁 Config Dir: {self.config_dir.absolute()}")
        else:
            print("❌ No configuration found")
    
    def setup(self) -> None:
        """Interactive setup wizard."""
        print("🔧 Telegram Calendar Bot Setup")
        print("=" * 40)
        
        # Create config directory if it doesn't exist
        self.config_dir.mkdir(exist_ok=True)
        
        # Get bot token
        token = input("🤖 Enter your Telegram Bot Token: ").strip()
        if not token:
            print("❌ Token is required")
            return
            
        # Google Calendar setup
        use_calendar = input("📅 Enable Google Calendar integration? (y/N): ").lower().startswith('y')
        
        calendar_id = ""
        credentials_file = ""
        if use_calendar:
            calendar_id = input("📋 Google Calendar ID (optional): ").strip()
            credentials_file = input("🔐 Path to Google credentials JSON (optional): ").strip()
        
        # Rate limiting
        rate_limit = input("⏰ Rate limit per user per minute (default: 20): ").strip() or "20"
        
        # Log level
        log_level = input("📝 Log level (DEBUG/INFO/WARNING/ERROR, default: INFO): ").strip().upper() or "INFO"
        
        # Create .env file
        env_content = f"""# Telegram Calendar Bot Configuration
TELEGRAM_BOT_TOKEN={token}
GOOGLE_CALENDAR_ID={calendar_id}
GOOGLE_CREDENTIALS_FILE={credentials_file}
RATE_LIMIT_PER_MINUTE={rate_limit}
LOG_LEVEL={log_level}
"""
        
        self.env_file.write_text(env_content)
        print(f"✅ Configuration saved to {self.env_file}")
        
        # Create basic config.json
        config = {
            "bot_name": "Telegram Calendar Bot",
            "version": "1.0.0",
            "features": {
                "google_calendar": use_calendar,
                "ocr_service": True,
                "nlp_service": True,
                "speech_service": True
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
            
        print(f"✅ Configuration file created: {self.config_file}")
        print("\n🚀 Setup complete! You can now run 'bot start' to launch the bot")
    
    def config_cmd(self, key: Optional[str] = None, value: Optional[str] = None) -> None:
        """Manage configuration settings."""
        if not self.env_file.exists():
            print("❌ Configuration not found. Run 'bot setup' first")
            return
            
        if key is None:
            # Show all configuration
            print("⚙️ Current Configuration:")
            with open(self.env_file) as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        print(f"  {line.strip()}")
        elif value is None:
            # Show specific key
            load_dotenv(self.env_file)
            val = os.getenv(key, "Not set")
            if 'token' in key.lower():
                val = val[:8] + '...' + val[-8:] if len(val) > 16 else val
            print(f"{key} = {val}")
        else:
            # Set key=value
            self._update_env_file(key, value)
            print(f"✅ Updated {key}")
    
    def logs(self, tail: int = 50) -> None:
        """Show bot logs."""
        if not self.log_file.exists():
            print("❌ Log file not found")
            return
            
        try:
            subprocess.run(['tail', f'-{tail}', str(self.log_file)], check=True)
        except subprocess.CalledProcessError:
            # Fallback for systems without tail
            with open(self.log_file) as f:
                lines = f.readlines()
                for line in lines[-tail:]:
                    print(line.rstrip())
    
    def is_running(self) -> bool:
        """Check if bot is running."""
        if not self.pid_file.exists():
            return False
            
        try:
            pid = int(self.pid_file.read_text().strip())
            return psutil.pid_exists(pid)
        except (ValueError, FileNotFoundError):
            return False
    
    def get_pid(self) -> Optional[int]:
        """Get bot PID if running."""
        if not self.pid_file.exists():
            return None
            
        try:
            return int(self.pid_file.read_text().strip())
        except (ValueError, FileNotFoundError):
            return None
    
    def _start_daemon(self) -> None:
        """Start bot in daemon mode."""
        # Fork to background
        pid = os.fork()
        if pid > 0:
            # Parent process
            self.pid_file.write_text(str(pid))
            print(f"✅ Bot started in background (PID: {pid})")
            return
            
        # Child process - become daemon
        os.setsid()
        
        # Redirect stdio to log file
        self.log_file.touch()
        with open(self.log_file, 'a') as f:
            os.dup2(f.fileno(), sys.stdout.fileno())
            os.dup2(f.fileno(), sys.stderr.fileno())
            
        self._run_bot()
    
    def _start_foreground(self) -> None:
        """Start bot in foreground mode."""
        # Save PID
        self.pid_file.write_text(str(os.getpid()))
        
        try:
            self._run_bot()
        except KeyboardInterrupt:
            print("\n🛑 Bot stopped by user")
        finally:
            self.pid_file.unlink(missing_ok=True)
    
    def _run_bot(self) -> None:
        """Run the actual bot."""
        load_dotenv(self.env_file)
        
        # Setup logging
        log_level = os.getenv('LOG_LEVEL', 'INFO')
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(self.log_file)
            ]
        )
        
        # Create and start bot
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        rate_limit = int(os.getenv('RATE_LIMIT_PER_MINUTE', '20'))
        
        bot = create_telegram_bot(token, rate_limit_per_minute=rate_limit)
        
        logger.info("Starting Telegram Calendar Bot...")
        asyncio.run(bot.start_polling())
    
    def _show_log_tail(self, lines: int = 10) -> None:
        """Show last N lines of log file."""
        try:
            with open(self.log_file) as f:
                tail_lines = f.readlines()[-lines:]
                for line in tail_lines:
                    print(f"  {line.rstrip()}")
        except Exception as e:
            print(f"❌ Error reading log: {e}")
    
    def _update_env_file(self, key: str, value: str) -> None:
        """Update a key in the .env file."""
        lines = []
        found = False
        
        if self.env_file.exists():
            with open(self.env_file) as f:
                lines = f.readlines()
        
        # Update existing key or add new one
        for i, line in enumerate(lines):
            if line.startswith(f"{key}="):
                lines[i] = f"{key}={value}\n"
                found = True
                break
        
        if not found:
            lines.append(f"{key}={value}\n")
        
        self.env_file.write_text(''.join(lines))


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Telegram Calendar Bot CLI",
        prog="bot"
    )
    parser.add_argument(
        "--config-dir", 
        default=".",
        help="Configuration directory (default: current directory)"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Start command
    start_parser = subparsers.add_parser("start", help="Start the bot")
    start_parser.add_argument(
        "--daemon", "-d",
        action="store_true",
        help="Run in background (daemon mode)"
    )
    
    # Stop command
    subparsers.add_parser("stop", help="Stop the bot")
    
    # Status command  
    subparsers.add_parser("status", help="Show bot status")
    
    # Setup command
    subparsers.add_parser("setup", help="Interactive setup wizard")
    
    # Config command
    config_parser = subparsers.add_parser("config", help="Manage configuration")
    config_parser.add_argument("key", nargs="?", help="Configuration key")
    config_parser.add_argument("value", nargs="?", help="Configuration value")
    
    # Logs command
    logs_parser = subparsers.add_parser("logs", help="Show bot logs")
    logs_parser.add_argument(
        "--tail", "-n",
        type=int,
        default=50,
        help="Number of lines to show (default: 50)"
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = BotManager(args.config_dir)
    
    try:
        if args.command == "start":
            manager.start(daemon=args.daemon)
        elif args.command == "stop":
            manager.stop()
        elif args.command == "status":
            manager.status()
        elif args.command == "setup":
            manager.setup()
        elif args.command == "config":
            manager.config_cmd(args.key, args.value)
        elif args.command == "logs":
            manager.logs(args.tail)
    except KeyboardInterrupt:
        print("\n🛑 Operation cancelled")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()