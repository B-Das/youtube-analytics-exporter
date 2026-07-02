import os
import re

exporters_dir = r"c:\Users\biraj\Desktop\ytAnalyticsdata\exporters"
files = [f for f in os.listdir(exporters_dir) if f.endswith(".py") and f != "base.py" and f != "__init__.py" and f != "registry.py"]

for filename in files:
    filepath = os.path.join(exporters_dir, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Remove import
    content = content.replace("from mock_data_generator import MockDataGenerator\n", "")
    content = content.replace("from mock_data_generator import MockDataGenerator", "")

    # 2. Modify signature
    content = content.replace(",\n        use_mock: bool = True", "")
    content = content.replace(",\n        use_mock: bool = False", "")
    content = content.replace(", use_mock: bool = True", "")
    content = content.replace(", use_mock: bool = False", "")

    # 3. Modify logic: replace the check and the catch-all
    # Find what function was called, e.g. MockDataGenerator.generate_overview
    match = re.search(r"MockDataGenerator\.generate_\w+\(start_date, end_date\)", content)
    if match:
        generator_call = match.group(0)
        # Replace the header check
        header_pattern = rf"if use_mock or analytics_service is None:\s+return {re.escape(generator_call)}"
        content = re.sub(header_pattern, "if analytics_service is None:\n            raise ValueError('YouTube API service is not connected.')", content)
        
        header_pattern_2 = rf"if use_mock or analytics_service is None:\s+return MockDataGenerator\.generate_\w+\(start_date, end_date\)"
        content = re.sub(header_pattern_2, "if analytics_service is None:\n            raise ValueError('YouTube API service is not connected.')", content)

        # Replace the catch block
        catch_pattern = rf"except Exception:\s+return {re.escape(generator_call)}"
        content = re.sub(catch_pattern, "except Exception as e:\n            raise RuntimeError(f'API Query failed: {e}')", content)

        catch_pattern_2 = rf"except Exception as e:\s+return {re.escape(generator_call)}"
        content = re.sub(catch_pattern_2, "except Exception as e:\n            raise RuntimeError(f'API Query failed: {e}')", content)

        catch_pattern_3 = rf"except Exception:\s+return MockDataGenerator\.generate_\w+\(start_date, end_date\)"
        content = re.sub(catch_pattern_3, "except Exception as e:\n            raise RuntimeError(f'API Query failed: {e}')", content)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

print("Exporters successfully cleaned up of mock data fallbacks!")
