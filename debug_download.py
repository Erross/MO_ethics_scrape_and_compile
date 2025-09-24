"""
Debug version to test save dialog issues
Let's figure out why files aren't being created
"""

import time
import pyautogui
from pathlib import Path


def debug_save_dialog():
    """Test the save dialog in isolation"""
    downloads_dir = Path.cwd() / "downloads"
    downloads_dir.mkdir(exist_ok=True)

    print("🧪 === SAVE DIALOG DEBUG TEST ===")
    print("1. Manually open a PDF in your browser")
    print("2. Press Enter when ready to test save dialog...")
    input("Press Enter when PDF is open...")

    # Test with shorter filename first
    short_filename = "test_report_123456.pdf"
    full_path = downloads_dir / short_filename

    print(f"\n🎯 Testing save with: {short_filename}")
    print(f"Full path: {full_path}")
    print("Starting in 3 seconds...")

    for i in range(3, 0, -1):
        print(f"{i}...")
        time.sleep(1)

    try:
        print("Step 1: Pressing Ctrl+S...")
        pyautogui.hotkey('ctrl', 's')
        time.sleep(3)  # Longer wait

        print("Step 2: Taking screenshot...")
        screenshot = pyautogui.screenshot()
        screenshot.save("debug_screenshot.png")
        print("Screenshot saved as debug_screenshot.png")

        print("Step 3: Clearing field with Ctrl+A...")
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(1)

        print(f"Step 4: Typing path: {full_path}")
        pyautogui.write(str(full_path), interval=0.1)
        time.sleep(2)

        print("Step 5: Taking another screenshot...")
        screenshot2 = pyautogui.screenshot()
        screenshot2.save("debug_screenshot2.png")
        print("Screenshot saved as debug_screenshot2.png")

        print("Step 6: Pressing Enter...")
        pyautogui.press('enter')

        print("Step 7: Waiting 10 seconds for download...")
        for i in range(10, 0, -1):
            if full_path.exists():
                size = full_path.stat().st_size
                print(f"✅ SUCCESS! File created: {size:,} bytes")
                return True
            print(f"Waiting... {i}s")
            time.sleep(1)

        print("❌ FAILED: File was not created")
        return False

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_long_filename():
    """Test if long filenames are the problem"""
    downloads_dir = Path.cwd() / "downloads"

    # Test creating a file with the same long name
    long_filename = "Francis_Howell_Families_2025_24_Hour_Expenditure_Report-482025_General_Municipal_03-31-2025_249589.pdf"

    print(f"\n🧪 Testing long filename creation...")
    print(f"Filename length: {len(long_filename)} characters")
    print(f"Filename: {long_filename}")

    try:
        test_path = downloads_dir / long_filename
        test_path.write_text("test content")
        print(f"✅ Long filename works fine!")
        test_path.unlink()  # Delete test file
    except Exception as e:
        print(f"❌ Long filename failed: {e}")


if __name__ == "__main__":
    test_long_filename()
    debug_save_dialog()