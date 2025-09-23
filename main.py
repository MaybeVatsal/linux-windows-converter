import os
import subprocess
import sys
import signal
import shlex
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

command_mapping = {
    "filesystem": {
        "ls": {"cmd": ["cmd", "/c", "dir"], "help": "List directory contents", "preserve_args": True},
        "ls -l": {"cmd": ["cmd", "/c", "dir"], "help": "List in long format", "preserve_args": False},
        "ls -la": {"cmd": ["cmd", "/c", "dir", "/a"], "help": "List all files including hidden", "preserve_args": False},
        "ls -al": {"cmd": ["cmd", "/c", "dir", "/a"], "help": "List all files including hidden", "preserve_args": False},
        "ls -lh": {"cmd": ["cmd", "/c", "dir"], "help": "List with human readable sizes", "preserve_args": False},
        "ll": {"cmd": ["cmd", "/c", "dir"], "help": "Long listing format", "preserve_args": False},
        "pwd": {"cmd": [], "help": "Print working directory", "preserve_args": False, "internal": True},
        "cd": {"cmd": [], "help": "Change directory", "preserve_args": False, "internal": True},
        "clear": {"cmd": ["cmd", "/c", "cls"], "help": "Clear the screen", "preserve_args": False},
        "cls": {"cmd": ["cmd", "/c", "cls"], "help": "Clear the screen", "preserve_args": False},
    },
    
    "file_operations": {
        "cat": {"cmd": ["cmd", "/c", "type"], "help": "Concatenate and display file content", "preserve_args": True},
        "tac": {"cmd": [], "help": "Reverse cat (internal)", "preserve_args": False, "internal": True},
        "more": {"cmd": ["more"], "help": "View file content page by page", "preserve_args": True},
        "less": {"cmd": ["more"], "help": "View file content with backward navigation", "preserve_args": True},
        "head": {"cmd": [], "help": "Display first lines of file", "preserve_args": False, "internal": True},
        "tail": {"cmd": [], "help": "Display last lines of file", "preserve_args": False, "internal": True},
        "touch": {"cmd": [], "help": "Create empty file or update timestamp", "preserve_args": False, "internal": True},
        "mkdir": {"cmd": ["cmd", "/c", "mkdir"], "help": "Create directory", "preserve_args": True},
        "rm": {"cmd": ["cmd", "/c", "del"], "help": "Remove files", "preserve_args": True},
        "rmdir": {"cmd": ["cmd", "/c", "rmdir"], "help": "Remove directory", "preserve_args": True},
        "rm -rf": {"cmd": ["cmd", "/c", "rmdir", "/s", "/q"], "help": "Force remove directory recursively", "preserve_args": True},
        "cp": {"cmd": ["cmd", "/c", "copy"], "help": "Copy files", "preserve_args": True},
        "mv": {"cmd": ["cmd", "/c", "move"], "help": "Move files", "preserve_args": True},
        "find": {"cmd": ["cmd", "/c", "dir", "/s"], "help": "Find files", "preserve_args": True},
        "grep": {"cmd": ["findstr"], "help": "Search text in files", "preserve_args": True},
        "egrep": {"cmd": ["findstr"], "help": "Extended grep", "preserve_args": True},
        "fgrep": {"cmd": ["findstr"], "help": "Fixed string grep", "preserve_args": True},
        "wc": {"cmd": [], "help": "Word count", "preserve_args": False, "internal": True},
        "sort": {"cmd": ["sort"], "help": "Sort lines of text", "preserve_args": True},
        "uniq": {"cmd": [], "help": "Remove duplicate lines", "preserve_args": False, "internal": True},
        "diff": {"cmd": ["fc"], "help": "Compare files", "preserve_args": True},
        "cmp": {"cmd": ["fc"], "help": "Compare files byte by byte", "preserve_args": True},
        "file": {"cmd": [], "help": "Determine file type", "preserve_args": False, "internal": True},
        "stat": {"cmd": [], "help": "Display file status", "preserve_args": False, "internal": True},
        "ln": {"cmd": ["mklink"], "help": "Create links", "preserve_args": True},
        "chmod": {"cmd": ["icacls"], "help": "Change file permissions", "preserve_args": True},
        "chown": {"cmd": [], "help": "Change file owner", "preserve_args": False, "internal": True},
        "chgrp": {"cmd": [], "help": "Change file group", "preserve_args": False, "internal": True},
        "df": {"cmd": ["fsutil", "volume", "diskfree"], "help": "Display disk space usage", "preserve_args": True},
        "du": {"cmd": [], "help": "Estimate file space usage", "preserve_args": False, "internal": True},
        "mount": {"cmd": ["mountvol"], "help": "Mount file systems", "preserve_args": True},
        "umount": {"cmd": ["mountvol"], "help": "Unmount file systems", "preserve_args": True},
    },
    
    "text_processing": {
        "awk": {"cmd": [], "help": "Pattern scanning and processing", "preserve_args": False, "internal": True},
        "sed": {"cmd": [], "help": "Stream editor", "preserve_args": False, "internal": True},
        "cut": {"cmd": ["forfiles"], "help": "Remove sections from lines", "preserve_args": True},
        "paste": {"cmd": [], "help": "Merge lines of files", "preserve_args": False, "internal": True},
        "join": {"cmd": [], "help": "Join lines on common field", "preserve_args": False, "internal": True},
        "tr": {"cmd": [], "help": "Translate or delete characters", "preserve_args": False, "internal": True},
        "tee": {"cmd": ["tee"], "help": "Redirect output to multiple files", "preserve_args": True},
        "xargs": {"cmd": [], "help": "Build and execute commands", "preserve_args": False, "internal": True},
    },
    
    "process_management": {
        "ps": {"cmd": ["tasklist"], "help": "Display running processes", "preserve_args": False},
        "ps aux": {"cmd": ["tasklist", "/v"], "help": "Display detailed process information", "preserve_args": False},
        "ps -ef": {"cmd": ["tasklist"], "help": "Display all processes", "preserve_args": False},
        "ps -e": {"cmd": ["tasklist"], "help": "Display all processes", "preserve_args": False},
        "kill": {"cmd": ["taskkill"], "help": "Terminate processes", "preserve_args": True},
        "killall": {"cmd": ["taskkill", "/im"], "help": "Kill processes by name", "preserve_args": True},
        "pkill": {"cmd": ["taskkill", "/im"], "help": "Kill processes by name", "preserve_args": True},
        "top": {"cmd": ["tasklist"], "help": "Display running processes", "preserve_args": False},
        "htop": {"cmd": ["tasklist"], "help": "Interactive process viewer", "preserve_args": False},
        "bg": {"cmd": [], "help": "Run job in background", "preserve_args": False, "internal": True},
        "fg": {"cmd": [], "help": "Run job in foreground", "preserve_args": False, "internal": True},
        "jobs": {"cmd": [], "help": "List jobs", "preserve_args": False, "internal": True},
        "nice": {"cmd": ["start"], "help": "Run with modified scheduling priority", "preserve_args": True},
        "renice": {"cmd": ["wmic", "process"], "help": "Change priority of running process", "preserve_args": True},
        "nohup": {"cmd": ["start"], "help": "Run immune to hangups", "preserve_args": True},
        "timeout": {"cmd": ["timeout"], "help": "Run with time limit", "preserve_args": True},
        "sleep": {"cmd": ["timeout"], "help": "Delay for specified time", "preserve_args": True},
        "wait": {"cmd": [], "help": "Wait for process completion", "preserve_args": False, "internal": True},
        "sudo": {"cmd": [], "help": "Execute command as administrator", "preserve_args": False, "internal": True},
        "su": {"cmd": [], "help": "Switch user or run as administrator", "preserve_args": False, "internal": True},
    },
    
    "system_info": {
        "whoami": {"cmd": ["whoami"], "help": "Display current user", "preserve_args": False},
        "id": {"cmd": ["whoami"], "help": "Display user identity", "preserve_args": False},
        "uname": {"cmd": ["cmd", "/c", "ver"], "help": "Display system information", "preserve_args": False},
        "uname -a": {"cmd": ["systeminfo"], "help": "Display detailed system information", "preserve_args": False},
        "uname -r": {"cmd": ["cmd", "/c", "ver"], "help": "Display kernel version", "preserve_args": False},
        "uname -s": {"cmd": ["cmd", "/c", "ver"], "help": "Display system name", "preserve_args": False},
        "date": {"cmd": ["cmd", "/c", "date", "/t"], "help": "Display current date", "preserve_args": False},
        "time": {"cmd": ["cmd", "/c", "time", "/t"], "help": "Display current time", "preserve_args": False},
        "cal": {"cmd": [], "help": "Display calendar", "preserve_args": False, "internal": True},
        "uptime": {"cmd": ["systeminfo"], "help": "Show system uptime", "preserve_args": False},
        "w": {"cmd": ["net", "session"], "help": "Show logged in users and activity", "preserve_args": False},
        "who": {"cmd": ["query", "user"], "help": "Display logged in users", "preserve_args": False},
        "users": {"cmd": ["query", "user"], "help": "Display logged in users", "preserve_args": False},
        "last": {"cmd": [], "help": "Show last logged in users", "preserve_args": False, "internal": True},
        "finger": {"cmd": [], "help": "User information lookup", "preserve_args": False, "internal": True},
        "env": {"cmd": ["set"], "help": "Display environment variables", "preserve_args": False},
        "printenv": {"cmd": ["set"], "help": "Print environment variables", "preserve_args": False},
        "set": {"cmd": ["set"], "help": "Set or display environment variables", "preserve_args": False},
        "hostname": {"cmd": ["hostname"], "help": "Display system hostname", "preserve_args": False},
        "domainname": {"cmd": ["net", "config", "workstation"], "help": "Display domain name", "preserve_args": False},
        "dnsdomainname": {"cmd": ["ipconfig", "/all"], "help": "Display DNS domain name", "preserve_args": False},
        "arch": {"cmd": ["echo", "%PROCESSOR_ARCHITECTURE%"], "help": "Display machine architecture", "preserve_args": False},
    },
    
    "network": {
        "ifconfig": {"cmd": ["ipconfig"], "help": "Display network configuration", "preserve_args": True},
        "ipconfig": {"cmd": ["ipconfig"], "help": "Display network configuration", "preserve_args": True},
        "ip": {"cmd": [], "help": "Show/manipulate routing, devices", "preserve_args": False, "internal": True},
        "ping": {"cmd": ["ping"], "help": "Test network connectivity", "preserve_args": True},
        "ping6": {"cmd": ["ping", "-6"], "help": "Test IPv6 connectivity", "preserve_args": True},
        "traceroute": {"cmd": ["tracert"], "help": "Trace route to host", "preserve_args": True},
        "tracert": {"cmd": ["tracert"], "help": "Trace route to host", "preserve_args": True},
        "netstat": {"cmd": ["netstat"], "help": "Display network statistics", "preserve_args": True},
        "ss": {"cmd": ["netstat"], "help": "Socket statistics", "preserve_args": True},
        "route": {"cmd": ["route"], "help": "Show/manipulate IP routing table", "preserve_args": True},
        "arp": {"cmd": ["arp"], "help": "Manipulate system ARP cache", "preserve_args": True},
        "host": {"cmd": ["nslookup"], "help": "DNS lookup utility", "preserve_args": True},
        "nslookup": {"cmd": ["nslookup"], "help": "Query Internet name servers", "preserve_args": True},
        "dig": {"cmd": ["nslookup"], "help": "DNS lookup utility", "preserve_args": True},
        "telnet": {"cmd": ["telnet"], "help": "User interface to TELNET", "preserve_args": True},
        "ssh": {"cmd": ["ssh"], "help": "OpenSSH SSH client", "preserve_args": True},
        "scp": {"cmd": [], "help": "Secure copy", "preserve_args": False, "internal": True},
        "ftp": {"cmd": ["ftp"], "help": "Internet file transfer program", "preserve_args": True},
        "wget": {"cmd": ["curl"], "help": "Non-interactive network downloader", "preserve_args": True},
        "curl": {"cmd": ["curl"], "help": "Transfer data from or to a server", "preserve_args": True},
        "nc": {"cmd": [], "help": "Netcat - networking utility", "preserve_args": False, "internal": True},
        "netcat": {"cmd": [], "help": "Netcat - networking utility", "preserve_args": False, "internal": True},
    },
    
    "user_management": {
        "passwd": {"cmd": [], "help": "Change user password", "preserve_args": False, "internal": True},
        "useradd": {"cmd": ["net", "user"], "help": "Create new user", "preserve_args": True},
        "adduser": {"cmd": ["net", "user"], "help": "Create new user", "preserve_args": True},
        "userdel": {"cmd": ["net", "user"], "help": "Delete user", "preserve_args": True},
        "deluser": {"cmd": ["net", "user"], "help": "Delete user", "preserve_args": True},
        "usermod": {"cmd": ["net", "user"], "help": "Modify user account", "preserve_args": True},
        "groupadd": {"cmd": ["net", "localgroup"], "help": "Create new group", "preserve_args": True},
        "addgroup": {"cmd": ["net", "localgroup"], "help": "Create new group", "preserve_args": True},
        "groupdel": {"cmd": ["net", "localgroup"], "help": "Delete group", "preserve_args": True},
        "delgroup": {"cmd": ["net", "localgroup"], "help": "Delete group", "preserve_args": True},
        "groupmod": {"cmd": ["net", "localgroup"], "help": "Modify group", "preserve_args": True},
        "groups": {"cmd": ["net", "user"], "help": "Display user groups", "preserve_args": True},
        "id": {"cmd": ["whoami"], "help": "Display user and group IDs", "preserve_args": False},
        "lastlog": {"cmd": [], "help": "Reports last login times", "preserve_args": False, "internal": True},
        "logname": {"cmd": ["echo", "%USERNAME%"], "help": "Display current login name", "preserve_args": False},
    },
    
    "package_management": {
        "apt": {"cmd": ["winget"], "help": "Package management utility", "preserve_args": True},
        "apt-get": {"cmd": ["winget"], "help": "Package management utility", "preserve_args": True},
        "yum": {"cmd": ["winget"], "help": "Package manager", "preserve_args": True},
        "dnf": {"cmd": ["winget"], "help": "Package manager", "preserve_args": True},
        "dpkg": {"cmd": [], "help": "Package manager for Debian", "preserve_args": False, "internal": True},
        "rpm": {"cmd": [], "help": "RPM Package Manager", "preserve_args": False, "internal": True},
        "pip": {"cmd": ["pip"], "help": "Python package installer", "preserve_args": True},
        "npm": {"cmd": ["npm"], "help": "Node package manager", "preserve_args": True},
    },
    
    "compression": {
        "tar": {"cmd": ["tar"], "help": "Archive utility", "preserve_args": True},
        "gzip": {"cmd": [], "help": "Compress files", "preserve_args": False, "internal": True},
        "gunzip": {"cmd": [], "help": "Decompress files", "preserve_args": False, "internal": True},
        "zip": {"cmd": ["tar", "-a"], "help": "Package and compress files", "preserve_args": True},
        "unzip": {"cmd": ["tar", "-xf"], "help": "Extract compressed files", "preserve_args": True},
        "7z": {"cmd": ["7z"], "help": "7-Zip archive utility", "preserve_args": True},
        "compress": {"cmd": [], "help": "Compress data", "preserve_args": False, "internal": True},
        "uncompress": {"cmd": [], "help": "Uncompress data", "preserve_args": False, "internal": True},
    },
    
    "windows_specific": {
        "tasklist": {"cmd": ["tasklist"], "help": "Display running processes", "preserve_args": True},
        "taskkill": {"cmd": ["taskkill"], "help": "Terminate processes", "preserve_args": True},
        "systeminfo": {"cmd": ["systeminfo"], "help": "Display system information", "preserve_args": True},
        "sfc": {"cmd": ["sfc"], "help": "System File Checker", "preserve_args": True},
        "chkdsk": {"cmd": ["chkdsk"], "help": "Check disk", "preserve_args": True},
        "diskpart": {"cmd": ["diskpart"], "help": "Disk partitioning utility", "preserve_args": True},
        "reg": {"cmd": ["reg"], "help": "Registry editor", "preserve_args": True},
        "sc": {"cmd": ["sc"], "help": "Service Control Manager", "preserve_args": True},
        "net": {"cmd": ["net"], "help": "Network command utility", "preserve_args": True},
        "wmic": {"cmd": ["wmic"], "help": "Windows Management Instrumentation", "preserve_args": True},
        "powershell": {"cmd": ["powershell"], "help": "PowerShell", "preserve_args": True},
        "cmd": {"cmd": ["cmd"], "help": "Command Prompt", "preserve_args": True},
        "color": {"cmd": ["color"], "help": "Change console color", "preserve_args": True},
        "title": {"cmd": ["title"], "help": "Set console title", "preserve_args": True},
        "ver": {"cmd": ["ver"], "help": "Display Windows version", "preserve_args": False},
        "vol": {"cmd": ["vol"], "help": "Display disk volume", "preserve_args": False},
        "label": {"cmd": ["label"], "help": "Change disk volume label", "preserve_args": True},
        "attrib": {"cmd": ["attrib"], "help": "Change file attributes", "preserve_args": True},
        "cacls": {"cmd": ["cacls"], "help": "Change file ACLs", "preserve_args": True},
        "icacls": {"cmd": ["icacls"], "help": "Change file ACLs", "preserve_args": True},
        "takeown": {"cmd": ["takeown"], "help": "Take ownership of files", "preserve_args": True},
        "robocopy": {"cmd": ["robocopy"], "help": "Robust file copy", "preserve_args": True},
        "xcopy": {"cmd": ["xcopy"], "help": "Extended file copy", "preserve_args": True},
        "tree": {"cmd": ["tree"], "help": "Display directory tree", "preserve_args": True},
        "fc": {"cmd": ["fc"], "help": "File compare", "preserve_args": True},
        "findstr": {"cmd": ["findstr"], "help": "Find strings in files", "preserve_args": True},
        "choice": {"cmd": ["choice"], "help": "Prompt user choice", "preserve_args": True},
        "timeout": {"cmd": ["timeout"], "help": "Wait specified time", "preserve_args": True},
        "schtasks": {"cmd": ["schtasks"], "help": "Schedule tasks", "preserve_args": True},
        "shutdown": {"cmd": ["shutdown"], "help": "Shutdown or restart computer", "preserve_args": True},
        "gpupdate": {"cmd": ["gpupdate"], "help": "Update group policy", "preserve_args": True},
        "gpresult": {"cmd": ["gpresult"], "help": "Display group policy results", "preserve_args": True},
    }
}


class LinuxCmdMiddleware:
    def __init__(self):
        self.current_dir = os.getcwd()
        self.running = True
        self.system_paths = self.get_system_paths()
        self._executable_cache: Dict[str, Optional[str]] = {}
        self.setup_signal_handlers()
        self.current_process = None
        self.is_elevated = self.check_admin_privileges()

    def check_admin_privileges(self) -> bool:
        """Check if the current process has administrator privileges"""
        try:
            if os.name == "nt":
                import ctypes

                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:
                return os.geteuid() == 0
        except:
            return False

    def setup_signal_handlers(self):
        """Set up signal handlers for Ctrl+C and other interrupts"""
        try:
            if os.name == "nt":
                # Windows signal handling - simplified approach
                def signal_handler(sig, frame):
                    if self.current_process:
                        try:
                            self.current_process.terminate()
                            self.current_process.wait(timeout=3)
                        except:
                            try:
                                self.current_process.kill()
                            except:
                                pass
                    print("^C")
                    self.current_process = None

                # Use signal.SIGINT which works on Windows in Python
                signal.signal(signal.SIGINT, signal_handler)
            else:
                # Unix signal handling
                def unix_handler(sig, frame):
                    if self.current_process:
                        self.current_process.terminate()
                    print("^C")

                signal.signal(signal.SIGINT, unix_handler)
        except Exception as e:
            print(f"Warning: Could not set up signal handlers: {e}")

    def get_system_paths(self) -> List[str]:
        """Get all directories in the system PATH with Windows System32 ensured"""
        path_env = os.environ.get('PATH', '')
        paths = [path.strip() for path in path_env.split(os.pathsep) if path.strip()]
        
        # Ensure Windows System32 paths are included
        if os.name == 'nt':
            system32_paths = [
                os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32'),
                os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32\\WindowsPowerShell\\v1.0'),
                os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32\\Wbem'),
            ]
            
            # Add Node.js paths if they exist
            possible_node_paths = [
                os.path.join(os.environ.get('ProgramFiles', 'C:\\Program Files'), 'nodejs'),
                os.path.join(os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)'), 'nodejs'),
            ]
            
            for node_path in possible_node_paths:
                if os.path.isdir(node_path) and node_path not in paths:
                    paths.append(node_path)
            
            for sys_path in system32_paths:
                if os.path.isdir(sys_path) and sys_path not in paths:
                    paths.insert(0, sys_path)  # Insert at beginning for priority
        
        return paths

    def find_executable(self, cmd: str) -> Optional[str]:
        """Check if a command exists in the system PATH with better Windows support"""
        if cmd in self._executable_cache:
            return self._executable_cache[cmd]

        # Debug: Uncomment this line to see what's being searched for
        # print(f"DEBUG: Looking for executable: {cmd}")

        # Check if the command is already a full path to an executable
        if os.path.isfile(cmd):
            if os.name == "nt" or os.access(cmd, os.X_OK):
                self._executable_cache[cmd] = cmd
                return cmd

        # Check in each directory of the PATH
        for path in self.system_paths:
            if not os.path.isdir(path):
                continue

            # On Windows, check with common extensions
            if os.name == "nt":
                # Check for various executable extensions
                extensions = ['.exe', '.cmd', '.bat', '.com', '.ps1', '']
                for ext in extensions:
                    executable_path = os.path.join(path, cmd + ext)
                    if os.path.isfile(executable_path):
                        # For .cmd and .bat files, we need to run them via cmd.exe
                        if ext in ['.cmd', '.bat']:
                            # Return the path as is, execution will handle it properly
                            self._executable_cache[cmd] = executable_path
                            return executable_path
                        else:
                            self._executable_cache[cmd] = executable_path
                            return executable_path
            else:
                # Unix-like systems
                executable_path = os.path.join(path, cmd)
                if os.path.isfile(executable_path) and os.access(executable_path, os.X_OK):
                    self._executable_cache[cmd] = executable_path
                    return executable_path

        # Special handling for Windows commands that might be in unusual locations
        if os.name == "nt":
            # Enhanced npm detection
            if cmd.lower() == 'npm':
                npm_paths = [
                    os.path.join(os.environ.get('APPDATA', ''), 'npm', 'npm.cmd'),
                    os.path.join(os.environ.get('APPDATA', ''), 'npm', 'npm'),
                    os.path.join(os.environ.get('ProgramFiles', ''), 'nodejs', 'npm.cmd'),
                    os.path.join(os.environ.get('ProgramFiles', ''), 'nodejs', 'npm'),
                    os.path.join(os.environ.get('ProgramFiles(x86)', ''), 'nodejs', 'npm.cmd'),
                    os.path.join(os.environ.get('ProgramFiles(x86)', ''), 'nodejs', 'npm'),
                    r'C:\Program Files\nodejs\npm.cmd',
                    r'C:\Program Files\nodejs\npm',
                    r'C:\Program Files (x86)\nodejs\npm.cmd',
                    r'C:\Program Files (x86)\nodejs\npm',
                ]
                
                for npm_path in npm_paths:
                    if os.path.isfile(npm_path):
                        self._executable_cache[cmd] = npm_path
                        return npm_path

        self._executable_cache[cmd] = None
        return None


    def display_help(self):
        """Display help information"""
        print("Linux to Windows Command Converter")
        print("Type Linux commands and they will be converted to Windows equivalents")
        print(
            f"\nCurrent privileges: {'Administrator' if self.is_elevated else 'Standard user'}"
        )
        print("\nSpecial commands:")
        print("  exit, quit - Exit the converter")
        print("  help - Show this help message")
        print("  win <command> - Execute a native Windows command")
        print("  path - Show current system PATH")
        print("  clear - Clear the screen")
        print("  sudo <command> - Run command with elevated privileges")
        print("  su [user] - Switch user or run as administrator")
        print("\nAvailable Linux commands:")

        for category, commands in command_mapping.items():
            print(f"\n{category.replace('_', ' ').title()}:")
            for cmd, info in commands.items():
                print(f"  {cmd:15} - {info['help']}")

    def find_matching_command(
        self, input_cmd: str
    ) -> Tuple[Optional[List[str]], bool, List[str], bool]:
        """
        Find the best matching command from the mapping

        Returns: (windows_command, preserve_args, arguments, is_internal)
        """
        try:
            cmd_parts = shlex.split(input_cmd)  # Use shlex for proper quote handling
        except ValueError as e:
            print(f"Error parsing command: {e}")
            return None, False, [], False

        if not cmd_parts:
            return None, False, [], False

        base_cmd = cmd_parts[0]
        args = cmd_parts[1:] if len(cmd_parts) > 1 else []

        # First try exact match
        for category in command_mapping.values():
            if input_cmd in category:
                info = category[input_cmd]
                return (
                    info["cmd"],
                    info.get("preserve_args", True),
                    args,
                    info.get("internal", False),
                )

        # Try to find the best match by command base
        best_match = None
        best_score = -1

        for category in command_mapping.values():
            for cmd_pattern, info in category.items():
                pattern_parts = cmd_pattern.split()

                # Check if our command starts with this pattern
                if len(cmd_parts) >= len(pattern_parts):
                    match = True
                    for i, part in enumerate(pattern_parts):
                        if i >= len(cmd_parts) or cmd_parts[i] != part:
                            match = False
                            break

                    if match:
                        # Score by specificity (longer patterns are better)
                        score = len(pattern_parts)
                        if score > best_score:
                            best_score = score
                            best_match = (info, cmd_parts[len(pattern_parts) :])

        if best_match:
            info, remaining_args = best_match
            return (
                info["cmd"],
                info.get("preserve_args", True),
                remaining_args,
                info.get("internal", False),
            )

        # If no pattern match, try just the base command
        for category in command_mapping.values():
            if base_cmd in category:
                info = category[base_cmd]
                return (
                    info["cmd"],
                    info.get("preserve_args", True),
                    args,
                    info.get("internal", False),
                )

        return None, False, args, False

    def execute_internal_command(self, command: str, args: List[str]) -> bool:
        """Execute internal commands that need special handling"""
        if command == "cd":
            return self.handle_cd_command(args)
        elif command == "touch":
            return self.handle_touch_command(args)
        elif command == "pwd":
            print(self.current_dir)
            return True
        elif command == "sudo":
            return self.handle_sudo_command(args)
        elif command == "su":
            return self.handle_su_command(args)
        elif command == "chown":
            return self.handle_chown_command(args)
        elif command == "passwd":
            return self.handle_passwd_command(args)
        return False

    def handle_sudo_command(self, args: List[str]) -> bool:
        """Handle sudo command - run with elevated privileges"""
        if not args:
            print("sudo: missing command")
            print("Usage: sudo <command> [arguments]")
            return False

        command_to_run = " ".join(args)

        if self.is_elevated:
            print(f"Already running as administrator. Executing: {command_to_run}")
            self.execute_command(command_to_run)
            return True
        else:
            print(f"Attempting to run with elevated privileges: {command_to_run}")
            return self.run_as_admin(command_to_run)

    def handle_su_command(self, args: List[str]) -> bool:
        """Handle su command - switch user or run as administrator"""
        if not args:
            # su without arguments typically switches to root/admin
            if self.is_elevated:
                print("Already running as administrator")
                return True
            else:
                print("Attempting to switch to administrator mode...")
                return self.run_as_admin("cmd.exe")
        else:
            target_user = args[0]
            if target_user == "root" or target_user == "administrator":
                if self.is_elevated:
                    print("Already running as administrator")
                    return True
                else:
                    print(f"Attempting to switch to {target_user}...")
                    return self.run_as_admin("cmd.exe")
            else:
                print(
                    f"User switching to '{target_user}' is not supported in this environment."
                )
                print("Only administrator/root switching is available.")
                return False

    def handle_chown_command(self, args: List[str]) -> bool:
        """Handle chown command - Windows equivalent using icacls"""
        if len(args) < 2:
            print("chown: missing operand")
            print("Usage: chown <user> <file>")
            return False

        user = args[0]
        files = args[1:]

        if not self.is_elevated:
            print("chown: requires administrator privileges. Use 'sudo chown'")
            return False

        success = True
        for file in files:
            try:
                file_path = (
                    file
                    if os.path.isabs(file)
                    else os.path.join(self.current_dir, file)
                )
                if not os.path.exists(file_path):
                    print(f"chown: cannot access '{file}': No such file or directory")
                    success = False
                    continue

                # Use icacls to change ownership
                result = subprocess.run(
                    ["icacls", file_path, "/setowner", user, "/T", "/C"],
                    capture_output=True,
                    text=True,
                )

                if result.returncode == 0:
                    print(f"Changed ownership of '{file}' to {user}")
                else:
                    print(
                        f"chown: failed to change ownership of '{file}': {result.stderr}"
                    )
                    success = False

            except Exception as e:
                print(f"chown: error processing '{file}': {e}")
                success = False

        return success

    def handle_passwd_command(self, args: List[str]) -> bool:
        """Handle passwd command - change user password"""
        if args:
            username = args[0]
            print(f"Changing password for user '{username}'")
            print("Note: Password change functionality is limited in this environment.")
            print("To change your Windows password, use:")
            print("  - net user [username] * (Command Prompt as admin)")
            print("  - CTRL+ALT+DEL -> Change Password")
            print("  - Windows Settings -> Accounts -> Sign-in options")
        else:
            print("Changing password for current user")
            print(
                "Note: Use Windows security options (CTRL+ALT+DEL) to change your password."
            )

        return True

    def run_as_admin(self, command: str) -> bool:
        """Run a command with administrator privileges"""
        if os.name != "nt":
            print("Administrator elevation is only supported on Windows")
            return False

        try:
            # For Windows, we can use runas command or show instructions
            print("\nTo run with administrator privileges:")
            print("1. Close this program")
            print("2. Right-click on Command Prompt or PowerShell")
            print("3. Select 'Run as administrator'")
            print("4. Navigate to this directory and run your command again")
            print(f"\nCommand that requires elevation: {command}")
            print("\nAlternatively, you can try:")
            print(f'  runas /user:Administrator "{command}"')

            # Offer to try runas if user wants
            try:
                response = (
                    input("\nTry to run with runas command? (y/N): ").strip().lower()
                )
                if response in ["y", "yes"]:
                    runas_cmd = f'runas /user:Administrator "{command}"'
                    os.system(runas_cmd)
                    return True
            except:
                pass

            return False

        except Exception as e:
            print(f"Error attempting elevation: {e}")
            return False

    def handle_cd_command(self, args: List[str]) -> bool:
        """Handle cd command with proper path resolution"""
        if not args:
            # cd without arguments goes to home directory
            new_dir = os.path.expanduser("~")
        else:
            target = args[0]
            if target == "~":
                new_dir = os.path.expanduser("~")
            else:
                if os.path.isabs(target):
                    new_dir = target
                else:
                    new_dir = os.path.normpath(os.path.join(self.current_dir, target))

        try:
            if os.path.exists(new_dir) and os.path.isdir(new_dir):
                os.chdir(new_dir)
                self.current_dir = os.getcwd()  # Update current directory
                return True
            else:
                print(f"cd: {new_dir}: No such directory")
                return False
        except Exception as e:
            print(f"cd: {e}")
            return False

    def handle_touch_command(self, args: List[str]) -> bool:
        """Handle touch command - create files or update timestamps"""
        if not args:
            print("touch: missing file operand")
            return False

        success = True
        for arg in args:
            try:
                if os.path.isabs(arg):
                    file_path = arg
                else:
                    file_path = os.path.join(self.current_dir, arg)

                if not os.path.exists(file_path):
                    Path(file_path).touch()
                else:
                    # Update timestamp
                    Path(file_path).touch()
            except Exception as e:
                print(f"touch: {arg}: {e}")
                success = False

        return success

    def execute_command_safely(
        self, cmd_args: List[str], use_shell: bool = False, elevated: bool = False
    ) -> int:
        """
        Execute a command safely without capturing output for interactive programs
        Returns the exit code
        """
        try:
            if not cmd_args:
                return 0

            # Debug output for troubleshooting
            # print(f"DEBUG: Executing: {cmd_args}", file=sys.stderr)

            if elevated and os.name == "nt" and not self.is_elevated:
                print("Warning: Cannot elevate privileges from within this process")
                print(
                    "Run this program as administrator for elevated command execution"
                )
                return 1

            if use_shell:
                # For shell builtins and complex commands
                cmd_line = " ".join(shlex.quote(str(arg)) for arg in cmd_args)
                self.current_process = subprocess.Popen(
                    cmd_line,
                    shell=True,
                    cwd=self.current_dir,
                    stdin=sys.stdin,
                    stdout=sys.stdout,
                    stderr=sys.stderr,
                )
            else:
                # For regular commands - much safer
                self.current_process = subprocess.Popen(
                    cmd_args,
                    cwd=self.current_dir,
                    stdin=sys.stdin,
                    stdout=sys.stdout,
                    stderr=sys.stderr,
                )

            # Wait for process to complete, allow signals to interrupt
            exit_code = self.current_process.wait()
            self.current_process = None
            return exit_code

        except KeyboardInterrupt:
            if self.current_process:
                try:
                    self.current_process.terminate()
                    self.current_process.wait(timeout=2)
                except:
                    try:
                        self.current_process.kill()
                    except:
                        pass
            self.current_process = None
            return 130  # Standard exit code for Ctrl+C
        except FileNotFoundError:
            print(f"Command not found: {cmd_args[0] if cmd_args else 'unknown'}")
            return 127
        except Exception as e:
            print(f"Error executing command: {e}", file=sys.stderr)
            self.current_process = None
            return 1

    def execute_command(self, command: str):
        """Execute a command with proper argument handling"""
        if not command.strip():
            return

        # Handle special internal commands
        if command.lower() in ["exit", "quit"]:
            self.running = False
            return

        if command.lower() == "help":
            self.display_help()
            return

        if command.lower() == "path":
            print("System PATH directories:")
            for i, path in enumerate(self.system_paths):
                print(f"{i+1:3d}. {path}")
            return

        if command.lower() == "clear":
            os.system("cls" if os.name == "nt" else "clear")
            return
        
        

        # Handle native Windows command execution
        if command.startswith("win "):
            win_cmd = command[4:]
            exit_code = self.execute_command_safely([win_cmd], use_shell=True)
            if exit_code != 0:
                print(f"Command exited with code {exit_code}", file=sys.stderr)
            return

        # Try to find a matching Linux command
        windows_cmd, preserve_args, args, is_internal = self.find_matching_command(
            command
        )

        if is_internal:
            # Handle internal commands like cd, touch, pwd, sudo, su
            self.execute_internal_command(command.split()[0], args)
            return

        if windows_cmd:
            # Build the command arguments
            if preserve_args and args:
                cmd_args = windows_cmd + args
            else:
                cmd_args = windows_cmd

            # Special handling for empty commands (internal only)
            if not cmd_args:
                return

            # Execute the command
            exit_code = self.execute_command_safely(cmd_args, use_shell=False)
            if exit_code != 0:
                print(f"Command exited with code {exit_code}", file=sys.stderr)
        else:
            # Check if this is a system command
            try:
                cmd_parts = shlex.split(command)
            except ValueError as e:
                print(f"Error parsing command: {e}")
                return

            if not cmd_parts:
                return

            base_cmd = cmd_parts[0]
            args = cmd_parts[1:] if len(cmd_parts) > 1 else []

            # Check if the command exists in the system PATH
            executable_path = self.find_executable(base_cmd)

            if executable_path:
                # Execute the system command directly
                cmd_args = [executable_path] + args
                exit_code = self.execute_command_safely(cmd_args, use_shell=False)
                if exit_code != 0:
                    print(f"Command exited with code {exit_code}", file=sys.stderr)
            else:
                print(f"Command not found: {base_cmd}")
                print("Type 'help' to see available commands")

    def run(self):
        """Main execution loop"""
        print("Linux to Windows Command Converter")
        print("Type 'help' for available commands, 'exit' to quit")
        if self.is_elevated:
            print("*** Running with administrator privileges ***")

        while self.running:
            try:
                # Display prompt with current directory and privilege indicator
                try:
                    home_dir = os.path.expanduser("~")
                    if self.current_dir.startswith(home_dir):
                        prompt_path = "~" + self.current_dir[len(home_dir) :]
                    else:
                        prompt_path = self.current_dir
                except:
                    prompt_path = self.current_dir

                # Use backslashes on Windows for better compatibility
                if os.name == "nt":
                    prompt_path = prompt_path.replace("/", "\\")

                # Add privilege indicator to prompt
                privilege_indicator = "#" if self.is_elevated else "$"
                prompt = f"[{prompt_path}]{privilege_indicator} "

                try:
                    command = input(prompt).strip()
                except KeyboardInterrupt:
                    print("^C")
                    continue
                except EOFError:
                    print("\nUse 'exit' to quit")
                    continue

                if command:
                    self.execute_command(command)

            except Exception as e:
                print(f"Unexpected error: {e}", file=sys.stderr)


def main():
    """Main entry point"""
    # Check if we're running on Windows
    if os.name != "nt":
        print("This tool is designed to run on Windows")
        print("Running on non-Windows system may have limited functionality")

    # Start the middleware
    middleware = LinuxCmdMiddleware()

    try:
        middleware.run()
    except KeyboardInterrupt:
        print("\nGoodbye!")
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
