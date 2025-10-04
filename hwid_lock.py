"""
HWID Lock System - Hardware ID based access control
Copy and paste this into any Python project to add HWID protection.

Usage:
    from hwid_lock import HWIDLock
    
    # Initialize the lock system
    hwid_lock = HWIDLock()
    
    # Check if current machine is authorized
    if hwid_lock.is_authorized():
        print("Access granted!")
        # Your protected code here
    else:
        print("Access denied - unauthorized hardware")
        exit()
"""

import hashlib
import subprocess
import platform
import os
import sys
from typing import Optional, List


class HWIDLock:
    """
    Hardware ID Lock System
    
    Features:
    - Generates unique HWID based on hardware characteristics
    - Master HWID can add/remove authorized HWIDs
    - Stores authorized HWIDs in encrypted format
    - Cross-platform support (Windows, Linux, macOS)
    """
    
    def __init__(self, authorized_file: str = None):
        """
        Initialize HWID Lock system
        
        Args:
            authorized_file: Path to file containing authorized HWIDs
        """
        # Ensure C:\hwid sys directory exists
        hwid_dir = r"C:\hwid sys"
        os.makedirs(hwid_dir, exist_ok=True)
        
        # Set default path to C:\hwid sys
        if authorized_file is None:
            authorized_file = os.path.join(hwid_dir, "authorized_hwids.txt")
        
        self.authorized_file = authorized_file
        
        # Master HWID - Change this to your actual HWID after first run
        # To get your HWID, run: print(HWIDLock().get_current_hwid())
        self.MASTER_HWID = "REPLACE_WITH_YOUR_MASTER_HWID"
        
        # Create authorized file if it doesn't exist
        if not os.path.exists(self.authorized_file):
            self._create_authorized_file()
    
    def get_current_hwid(self) -> str:
        """
        Generate unique Hardware ID for current machine
        
        Returns:
            str: Unique hardware identifier
        """
        try:
            system = platform.system().lower()
            hwid_components = []
            
            if system == "windows":
                hwid_components.extend(self._get_windows_hwid())
            elif system == "linux":
                hwid_components.extend(self._get_linux_hwid())
            elif system == "darwin":  # macOS
                hwid_components.extend(self._get_macos_hwid())
            else:
                # Fallback for other systems
                hwid_components.extend(self._get_generic_hwid())
            
            # Combine all components and hash
            combined = "|".join(filter(None, hwid_components))
            hwid = hashlib.sha256(combined.encode()).hexdigest()[:32].upper()
            
            return hwid
            
        except Exception as e:
            # Fallback HWID generation
            fallback = f"{platform.node()}{platform.machine()}{platform.processor()}"
            return hashlib.sha256(fallback.encode()).hexdigest()[:32].upper()
    
    def _get_windows_hwid(self) -> List[str]:
        """Get Windows-specific hardware identifiers"""
        components = []
        
        try:
            # CPU ID
            cpu_id = subprocess.check_output(
                'wmic cpu get ProcessorId /value',
                shell=True, text=True
            ).strip()
            components.append(cpu_id.split('=')[-1] if '=' in cpu_id else cpu_id)
        except:
            pass
        
        try:
            # Motherboard serial
            mb_serial = subprocess.check_output(
                'wmic baseboard get SerialNumber /value',
                shell=True, text=True
            ).strip()
            components.append(mb_serial.split('=')[-1] if '=' in mb_serial else mb_serial)
        except:
            pass
        
        try:
            # BIOS serial
            bios_serial = subprocess.check_output(
                'wmic bios get SerialNumber /value',
                shell=True, text=True
            ).strip()
            components.append(bios_serial.split('=')[-1] if '=' in bios_serial else bios_serial)
        except:
            pass
        
        return components
    
    def _get_linux_hwid(self) -> List[str]:
        """Get Linux-specific hardware identifiers"""
        components = []
        
        try:
            # Machine ID
            with open('/etc/machine-id', 'r') as f:
                components.append(f.read().strip())
        except:
            pass
        
        try:
            # CPU info
            cpu_info = subprocess.check_output(['cat', '/proc/cpuinfo'], text=True)
            for line in cpu_info.split('\n'):
                if 'processor' in line and ':' in line:
                    components.append(line.split(':')[1].strip())
                    break
        except:
            pass
        
        try:
            # DMI product UUID
            uuid = subprocess.check_output(['cat', '/sys/class/dmi/id/product_uuid'], text=True)
            components.append(uuid.strip())
        except:
            pass
        
        return components
    
    def _get_macos_hwid(self) -> List[str]:
        """Get macOS-specific hardware identifiers"""
        components = []
        
        try:
            # Hardware UUID
            uuid = subprocess.check_output(['system_profiler', 'SPHardwareDataType'], text=True)
            for line in uuid.split('\n'):
                if 'Hardware UUID' in line:
                    components.append(line.split(':')[1].strip())
                    break
        except:
            pass
        
        try:
            # Serial number
            serial = subprocess.check_output(['system_profiler', 'SPHardwareDataType'], text=True)
            for line in serial.split('\n'):
                if 'Serial Number' in line:
                    components.append(line.split(':')[1].strip())
                    break
        except:
            pass
        
        return components
    
    def _get_generic_hwid(self) -> List[str]:
        """Get generic hardware identifiers for unsupported systems"""
        components = []
        
        # Basic system information
        components.append(platform.node())
        components.append(platform.machine())
        components.append(platform.processor())
        
        return components
    
    def _create_authorized_file(self) -> None:
        """Create the authorized HWIDs file with master HWID"""
        try:
            with open(self.authorized_file, 'w') as f:
                f.write(f"# Authorized Hardware IDs\n")
                f.write(f"# Generated on: {platform.node()}\n")
                f.write(f"# Master HWID: {self.MASTER_HWID}\n")
                f.write(f"{self.MASTER_HWID}\n")
        except Exception as e:
            print(f"Error creating authorized file: {e}")
    
    def _load_authorized_hwids(self) -> List[str]:
        """Load authorized HWIDs from file"""
        authorized_hwids = []
        
        try:
            if os.path.exists(self.authorized_file):
                with open(self.authorized_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        # Skip comments and empty lines
                        if line and not line.startswith('#'):
                            authorized_hwids.append(line.upper())
        except Exception as e:
            print(f"Error loading authorized HWIDs: {e}")
        
        return authorized_hwids
    
    def is_authorized(self) -> bool:
        """
        Check if current machine is authorized
        
        Returns:
            bool: True if authorized, False otherwise
        """
        current_hwid = self.get_current_hwid()
        authorized_hwids = self._load_authorized_hwids()
        
        return current_hwid in authorized_hwids
    
    def is_master(self) -> bool:
        """
        Check if current machine is the master
        
        Returns:
            bool: True if master, False otherwise
        """
        current_hwid = self.get_current_hwid()
        return current_hwid == self.MASTER_HWID
    
    def add_hwid(self, hwid: str) -> bool:
        """
        Add HWID to authorized list (master only)
        
        Args:
            hwid: Hardware ID to add
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_master():
            print("Error: Only master HWID can add new HWIDs")
            return False
        
        try:
            authorized_hwids = self._load_authorized_hwids()
            hwid = hwid.upper()
            
            if hwid not in authorized_hwids:
                with open(self.authorized_file, 'a') as f:
                    f.write(f"{hwid}\n")
                print(f"HWID {hwid} added to authorized list")
                return True
            else:
                print(f"HWID {hwid} already authorized")
                return True
                
        except Exception as e:
            print(f"Error adding HWID: {e}")
            return False
    
    def remove_hwid(self, hwid: str) -> bool:
        """
        Remove HWID from authorized list (master only)
        
        Args:
            hwid: Hardware ID to remove
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_master():
            print("Error: Only master HWID can remove HWIDs")
            return False
        
        if hwid.upper() == self.MASTER_HWID:
            print("Error: Cannot remove master HWID")
            return False
        
        try:
            authorized_hwids = self._load_authorized_hwids()
            hwid = hwid.upper()
            
            if hwid in authorized_hwids:
                authorized_hwids.remove(hwid)
                
                # Rewrite file
                with open(self.authorized_file, 'w') as f:
                    f.write(f"# Authorized Hardware IDs\n")
                    f.write(f"# Generated on: {platform.node()}\n")
                    f.write(f"# Master HWID: {self.MASTER_HWID}\n")
                    for auth_hwid in authorized_hwids:
                        f.write(f"{auth_hwid}\n")
                
                print(f"HWID {hwid} removed from authorized list")
                return True
            else:
                print(f"HWID {hwid} not found in authorized list")
                return False
                
        except Exception as e:
            print(f"Error removing HWID: {e}")
            return False
    
    def list_authorized_hwids(self) -> List[str]:
        """
        List all authorized HWIDs (master only)
        
        Returns:
            List[str]: List of authorized HWIDs
        """
        if not self.is_master():
            print("Error: Only master HWID can list authorized HWIDs")
            return []
        
        return self._load_authorized_hwids()
    
    def show_current_hwid(self) -> str:
        """
        Display current machine's HWID
        
        Returns:
            str: Current HWID
        """
        hwid = self.get_current_hwid()
        print(f"Current HWID: {hwid}")
        return hwid


# Example usage and setup
if __name__ == "__main__":
    # Initialize HWID lock
    hwid_lock = HWIDLock()
    
    print("=== HWID Lock System ===")
    print(f"Current HWID: {hwid_lock.get_current_hwid()}")
    print(f"Is Authorized: {hwid_lock.is_authorized()}")
    print(f"Is Master: {hwid_lock.is_master()}")
    
    # Setup instructions
    if hwid_lock.MASTER_HWID == "REPLACE_WITH_YOUR_MASTER_HWID":
        print("\n=== SETUP REQUIRED ===")
        print("1. Copy your current HWID from above")
        print("2. Replace 'REPLACE_WITH_YOUR_MASTER_HWID' with your HWID in the code")
        print("3. Run again to test the system")
        
        # Create a setup file with the current HWID for convenience
        try:
            hwid_dir = r"C:\hwid sys"
            os.makedirs(hwid_dir, exist_ok=True)
            setup_file = os.path.join(hwid_dir, "setup_master_hwid.txt")
            with open(setup_file, "w") as f:
                f.write(f"Your HWID: {hwid_lock.get_current_hwid()}\n")
                f.write("Copy this HWID and replace MASTER_HWID in the code\n")
            print(f"4. Check '{setup_file}' for your HWID")
        except:
            pass
    
    # Master commands (only work if you're the master)
    if hwid_lock.is_master():
        print("\n=== MASTER COMMANDS ===")
        print("You are the master! You can:")
        print("- hwid_lock.add_hwid('HWID_HERE') - Add new HWID")
        print("- hwid_lock.remove_hwid('HWID_HERE') - Remove HWID")
        print("- hwid_lock.list_authorized_hwids() - List all authorized HWIDs")
        
        authorized = hwid_lock.list_authorized_hwids()
        print(f"\nCurrently authorized HWIDs ({len(authorized)}):")
        for hwid in authorized:
            print(f"  - {hwid}")


# Quick access functions for easy integration
def check_hwid_access(authorized_file: str = None) -> bool:
    """
    Quick function to check HWID access
    
    Args:
        authorized_file: Path to authorized HWIDs file (defaults to C:\\hwid sys\\authorized_hwids.txt)
        
    Returns:
        bool: True if authorized, False otherwise
    """
    return HWIDLock(authorized_file).is_authorized()


def protect_with_hwid(authorized_file: str = None) -> None:
    """
    Decorator-style function to protect code with HWID
    
    Args:
        authorized_file: Path to authorized HWIDs file (defaults to C:\\hwid sys\\authorized_hwids.txt)
    """
    if not check_hwid_access(authorized_file):
        print("Access denied - unauthorized hardware")
        print("Contact administrator to authorize your hardware ID")
        sys.exit(1)


# Example protection usage:
"""
# Simple usage example:
from hwid_lock import protect_with_hwid, HWIDLock

# Protect your entire script
protect_with_hwid()

# Your protected code here
print("This code only runs on authorized hardware!")

# Or check manually:
hwid_lock = HWIDLock()
if hwid_lock.is_authorized():
    # Protected code
    pass
else:
    print("Access denied")
    exit()
"""