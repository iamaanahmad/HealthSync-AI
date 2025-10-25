#!/usr/bin/env python3
"""
Test script to verify HealthSync project structure without external dependencies.
"""

import os
import sys

def test_directory_structure():
    """Test that required directories and files exist."""
    print("Testing project structure...")
    
    required_items = [
        # Core directories
        ("agents", "directory"),
        ("agents/patient_consent", "directory"),
        ("agents/data_custodian", "directory"), 
        ("agents/research_query", "directory"),
        ("agents/privacy", "directory"),
        ("agents/metta_integration", "directory"),
        ("shared", "directory"),
        ("shared/protocols", "directory"),
        ("shared/utils", "directory"),
        
        # Core files
        ("requirements.txt", "file"),
        ("config.py", "file"),
        ("setup.py", "file"),
        ("README.md", "file"),
        ("run_all_agents.py", "file"),
        
        # Shared module files
        ("shared/__init__.py", "file"),
        ("shared/base_agent.py", "file"),
        ("shared/protocols/__init__.py", "file"),
        ("shared/protocols/chat_protocol.py", "file"),
        ("shared/protocols/agent_messages.py", "file"),
        ("shared/utils/__init__.py", "file"),
        ("shared/utils/logging.py", "file"),
        ("shared/utils/error_handling.py", "file"),
        
        # Agent files
        ("agents/__init__.py", "file"),
        ("agents/patient_consent/__init__.py", "file"),
        ("agents/patient_consent/agent.py", "file"),
        ("agents/data_custodian/__init__.py", "file"),
        ("agents/research_query/__init__.py", "file"),
        ("agents/privacy/__init__.py", "file"),
        ("agents/metta_integration/__init__.py", "file"),
    ]
    
    missing_items = []
    
    for item_path, item_type in required_items:
        if item_type == "directory":
            if not os.path.isdir(item_path):
                missing_items.append(f"Directory: {item_path}")
        elif item_type == "file":
            if not os.path.isfile(item_path):
                missing_items.append(f"File: {item_path}")
    
    if missing_items:
        print("❌ Missing items:")
        for item in missing_items:
            print(f"   - {item}")
        return False
    else:
        print("✅ All required directories and files exist!")
        return True

def test_file_contents():
    """Test that key files have expected content."""
    print("\nTesting file contents...")
    
    tests = []
    
    # Test requirements.txt
    try:
        with open("requirements.txt", "r") as f:
            content = f.read()
            if "uagents" in content and "pydantic" in content:
                tests.append(("requirements.txt", True, "Contains expected dependencies"))
            else:
                tests.append(("requirements.txt", False, "Missing expected dependencies"))
    except Exception as e:
        tests.append(("requirements.txt", False, f"Error reading file: {e}"))
    
    # Test config.py
    try:
        with open("config.py", "r") as f:
            content = f.read()
            if "AGENT_CONFIG" in content and "patient_consent" in content:
                tests.append(("config.py", True, "Contains agent configuration"))
            else:
                tests.append(("config.py", False, "Missing agent configuration"))
    except Exception as e:
        tests.append(("config.py", False, f"Error reading file: {e}"))
    
    # Test README.md
    try:
        with open("README.md", "r", encoding="utf-8") as f:
            content = f.read()
            if "HealthSync" in content and "ASI Alliance" in content:
                tests.append(("README.md", True, "Contains project information"))
            else:
                tests.append(("README.md", False, "Missing project information"))
    except Exception as e:
        tests.append(("README.md", False, f"Error reading file: {e}"))
    
    # Test base_agent.py
    try:
        with open("shared/base_agent.py", "r") as f:
            content = f.read()
            if "HealthSyncBaseAgent" in content and "uagents" in content:
                tests.append(("base_agent.py", True, "Contains base agent class"))
            else:
                tests.append(("base_agent.py", False, "Missing base agent class"))
    except Exception as e:
        tests.append(("base_agent.py", False, f"Error reading file: {e}"))
    
    all_passed = True
    for filename, passed, message in tests:
        if passed:
            print(f"✅ {filename}: {message}")
        else:
            print(f"❌ {filename}: {message}")
            all_passed = False
    
    return all_passed

def test_python_syntax():
    """Test that Python files have valid syntax."""
    print("\nTesting Python syntax...")
    
    python_files = [
        "config.py",
        "setup.py",
        "run_all_agents.py",
        "shared/base_agent.py",
        "shared/protocols/chat_protocol.py",
        "shared/protocols/agent_messages.py",
        "shared/utils/logging.py",
        "shared/utils/error_handling.py",
        "agents/patient_consent/agent.py"
    ]
    
    syntax_errors = []
    
    for file_path in python_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, "r") as f:
                    content = f.read()
                compile(content, file_path, "exec")
                print(f"✅ {file_path}: Valid syntax")
            except SyntaxError as e:
                syntax_errors.append(f"{file_path}: {e}")
                print(f"❌ {file_path}: Syntax error - {e}")
            except Exception as e:
                # Other errors (like import errors) are expected without dependencies
                print(f"⚠️  {file_path}: {e} (expected without dependencies)")
        else:
            syntax_errors.append(f"{file_path}: File not found")
            print(f"❌ {file_path}: File not found")
    
    return len(syntax_errors) == 0

def main():
    """Run all structure tests."""
    print("HealthSync Project Structure Verification")
    print("=" * 50)
    
    tests = [
        ("Directory Structure", test_directory_structure),
        ("File Contents", test_file_contents),
        ("Python Syntax", test_python_syntax)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            failed += 1
    
    print(f"\n" + "=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\n🎉 Project structure is complete!")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Run full tests: python test_setup.py")
        print("3. Start agents: python run_all_agents.py")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please check the project structure.")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)