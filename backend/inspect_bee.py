try:
    import beeai_framework

    print("beeai_framework imported successfully")
    print(dir(beeai_framework))
except ImportError as e:
    print(f"Error importing beeai_framework: {e}")
