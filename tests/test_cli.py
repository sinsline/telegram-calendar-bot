import pytest
import subprocess
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from cli import CLI, BotManager


class TestCLI:
    """Test suite for CLI interface"""
    
    def setup_method(self):
        """Setup test environment"""
        self.cli = CLI()
        
    def test_cli_initialization(self):
        """Test CLI initializes correctly"""
        assert self.cli is not None
        assert hasattr(self.cli, 'args')
        
    def test_parse_start_command(self):
        """Test parsing start command"""
        args = self.cli.parse_args(['start'])
        assert args.command == 'start'
        
    def test_parse_stop_command(self):
        """Test parsing stop command"""
        args = self.cli.parse_args(['stop'])
        assert args.command == 'stop'
        
    def test_parse_status_command(self):
        """Test parsing status command"""
        args = self.cli.parse_args(['status'])
        assert args.command == 'status'
        
    def test_parse_config_command(self):
        """Test parsing config command with subcommands"""
        args = self.cli.parse_args(['config', 'set', 'token', 'test-token'])
        assert args.command == 'config'
        assert args.config_action == 'set'
        assert args.key == 'token'
        assert args.value == 'test-token'
        
    def test_parse_config_get_command(self):
        """Test parsing config get command"""
        args = self.cli.parse_args(['config', 'get', 'token'])
        assert args.command == 'config'
        assert args.config_action == 'get'
        assert args.key == 'token'
        
    def test_parse_config_list_command(self):
        """Test parsing config list command"""
        args = self.cli.parse_args(['config', 'list'])
        assert args.command == 'config'
        assert args.config_action == 'list'
        
    def test_parse_setup_command(self):
        """Test parsing setup command"""
        args = self.cli.parse_args(['setup'])
        assert args.command == 'setup'
        
    def test_parse_invalid_command(self):
        """Test parsing invalid command raises SystemExit"""
        with pytest.raises(SystemExit):
            self.cli.parse_args(['invalid'])


class TestBotManager:
    """Test suite for BotManager"""
    
    def setup_method(self):
        """Setup test environment"""
        self.bot_manager = BotManager()
        
    def test_bot_manager_initialization(self):
        """Test BotManager initializes correctly"""
        assert self.bot_manager is not None
        assert hasattr(self.bot_manager, 'pid_file')
        assert hasattr(self.bot_manager, 'log_file')
        
    @patch('subprocess.Popen')
    def test_start_bot_success(self, mock_popen):
        """Test starting bot successfully"""
        mock_process = Mock()
        mock_process.pid = 12345
        mock_popen.return_value = mock_process
        
        with patch.object(self.bot_manager, 'is_running', return_value=False):
            result = self.bot_manager.start()
            assert result is True
            mock_popen.assert_called_once()
            
    def test_start_bot_already_running(self):
        """Test starting bot when already running"""
        with patch.object(self.bot_manager, 'is_running', return_value=True):
            result = self.bot_manager.start()
            assert result is False
            
    @patch('os.kill')
    def test_stop_bot_success(self, mock_kill):
        """Test stopping bot successfully"""
        with patch.object(self.bot_manager, 'is_running', return_value=True):
            with patch.object(self.bot_manager, 'get_pid', return_value=12345):
                result = self.bot_manager.stop()
                assert result is True
                mock_kill.assert_called_once_with(12345, 15)  # SIGTERM
                
    def test_stop_bot_not_running(self):
        """Test stopping bot when not running"""
        with patch.object(self.bot_manager, 'is_running', return_value=False):
            result = self.bot_manager.stop()
            assert result is False
            
    @patch('os.path.exists')
    @patch('builtins.open')
    def test_is_running_with_valid_pid(self, mock_open, mock_exists):
        """Test is_running with valid PID"""
        mock_exists.return_value = True
        mock_open.return_value.__enter__.return_value.read.return_value = '12345'
        
        with patch('os.kill') as mock_kill:
            mock_kill.side_effect = None  # Process exists
            result = self.bot_manager.is_running()
            assert result is True
            
    @patch('os.path.exists')
    def test_is_running_no_pid_file(self, mock_exists):
        """Test is_running when PID file doesn't exist"""
        mock_exists.return_value = False
        result = self.bot_manager.is_running()
        assert result is False
        
    def test_get_status_running(self):
        """Test get_status when bot is running"""
        with patch.object(self.bot_manager, 'is_running', return_value=True):
            with patch.object(self.bot_manager, 'get_pid', return_value=12345):
                status = self.bot_manager.get_status()
                assert status['running'] is True
                assert status['pid'] == 12345
                
    def test_get_status_not_running(self):
        """Test get_status when bot is not running"""
        with patch.object(self.bot_manager, 'is_running', return_value=False):
            status = self.bot_manager.get_status()
            assert status['running'] is False
            assert status['pid'] is None


class TestCLIIntegration:
    """Integration tests for CLI commands"""
    
    def setup_method(self):
        """Setup test environment"""
        self.cli = CLI()
        
    @patch.object(BotManager, 'start')
    def test_execute_start_command(self, mock_start):
        """Test executing start command"""
        mock_start.return_value = True
        args = self.cli.parse_args(['start'])
        
        with patch('builtins.print') as mock_print:
            self.cli.execute(args)
            mock_start.assert_called_once()
            mock_print.assert_called_with("✅ Bot started successfully")
            
    @patch.object(BotManager, 'stop')
    def test_execute_stop_command(self, mock_stop):
        """Test executing stop command"""
        mock_stop.return_value = True
        args = self.cli.parse_args(['stop'])
        
        with patch('builtins.print') as mock_print:
            self.cli.execute(args)
            mock_stop.assert_called_once()
            mock_print.assert_called_with("✅ Bot stopped successfully")
            
    @patch.object(BotManager, 'get_status')
    def test_execute_status_command(self, mock_get_status):
        """Test executing status command"""
        mock_get_status.return_value = {
            'running': True,
            'pid': 12345,
            'uptime': '2 days, 3:45:12',
            'memory_usage': '45.2 MB'
        }
        args = self.cli.parse_args(['status'])
        
        with patch('builtins.print') as mock_print:
            self.cli.execute(args)
            mock_get_status.assert_called_once()
            assert any('Status: Running' in str(call) for call in mock_print.call_args_list)


class TestConfigManager:
    """Test suite for configuration management"""
    
    def setup_method(self):
        """Setup test environment"""
        from cli import ConfigManager
        self.config_manager = ConfigManager()
        
    def test_config_manager_initialization(self):
        """Test ConfigManager initializes correctly"""
        assert self.config_manager is not None
        assert hasattr(self.config_manager, 'config_file')
        
    @patch('builtins.open')
    @patch('json.dump')
    def test_set_config_value(self, mock_dump, mock_open):
        """Test setting configuration value"""
        with patch.object(self.config_manager, 'load_config', return_value={}):
            result = self.config_manager.set('test_key', 'test_value')
            assert result is True
            
    @patch('builtins.open')
    @patch('json.load')
    def test_get_config_value(self, mock_load, mock_open):
        """Test getting configuration value"""
        mock_load.return_value = {'test_key': 'test_value'}
        value = self.config_manager.get('test_key')
        assert value == 'test_value'
        
    def test_get_nonexistent_config_value(self):
        """Test getting non-existent configuration value"""
        with patch.object(self.config_manager, 'load_config', return_value={}):
            value = self.config_manager.get('nonexistent_key')
            assert value is None