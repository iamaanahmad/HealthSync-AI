#!/usr/bin/env python3
"""
Check if required dependencies are installed and provide installation instructions.
"""

import sys
import subprocess
import importlib

def check_dependency(package_name, import_name=None):
    """Check if a package is installed."""
    if import_name is None:
        import_name = package_name
    
    try:
        importlib.import_module(import_name)
        print(f"✓ {package_name} is installed")
        return True
    except ImportError:
        print(f"✗ {package_name} is NOT installed")
        return False

def main():
    """Check all required dependencies."""
    print("HealthSync Dependency Check")
    print("=" * 40)
    
    # Core dependencies for basic functionality
    basic_deps = [
        ("pydantic", "pydantic"),
        ("structlog", "structlog"),
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"),
        ("cryptography", "cryptography"),
    ]
    
    # uAgents and Fetch.ai dependencies (may not be available via pip)
    advanced_deps = [
        ("uagents", "uagents"),
        ("fetchai-ledger-api", "fetchai_ledger_api"),
        ("cosmpy", "cosmpy"),
    ]
    
    print("\nChecking basic dependencies:")
    basic_missing = []
    for pkg, imp in basic_deps:
        if not check_dependency(pkg, imp):
            basic_missing.append(pkg)
    
    print("\nChecking advanced dependencies:")
    advanced_missing = []
    for pkg, imp in advanced_deps:
        if not check_dependency(pkg, imp):
            advanced_missing.append(pkg)
    
    print("\n" + "=" * 40)
    
    if basic_missing:
        print("❌ Missing basic dependencies:")
        for pkg in basic_missing:
            print(f"   - {pkg}")
        print("\nTo install basic dependencies:")
        print("pip install " + " ".join(basic_missing))
    else:
        print("✅ All basic dependencies are installed!")
    
    if advanced_missing:
        print("\n⚠️  Missing advanced dependencies:")
        for pkg in advanced_missing:
            print(f"   - {pkg}")
        print("\nTo install advanced dependencies:")
        print("pip install " + " ".join(advanced_missing))
        print("\nNote: Some packages may require specific installation methods.")
        print("Refer to the official documentation for uAgents and Fetch.ai packages.")
    else:
        print("✅ All advanced dependencies are installed!")
    
    if not basic_missing and not advanced_missing:
        print("\n🎉 All dependencies are ready! You can now run:")
        print("python test_setup.py")
    
    return len(basic_missing) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)