import os
import json
from transforms.registry import TRANSFORMS

class SchemaValidationError(Exception):
    pass

def validate_schema_file(filepath: str) -> dict:
    if not os.path.exists(filepath):
        raise SchemaValidationError(f"Schema file does not exist: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        schema = json.load(f)

    for field in ["id", "name", "filename", "columns"]:
        if field not in schema:
            raise SchemaValidationError(f"Missing mandatory top-level field '{field}' in {filepath}")

    seen_api_names = set()
    seen_display_names = set()

    for col in schema["columns"]:
        if "api_name" not in col or "display_name" not in col or "type" not in col:
            raise SchemaValidationError(f"Column missing mandatory keys in {filepath}: {col}")

        api_name = col["api_name"]
        display_name = col["display_name"]

        if api_name in seen_api_names:
            raise SchemaValidationError(f"Duplicate api_name '{api_name}' in {filepath}")
        if display_name in seen_display_names:
            raise SchemaValidationError(f"Duplicate display_name '{display_name}' in {filepath}")

        seen_api_names.add(api_name)
        seen_display_names.add(display_name)

        transform_name = col.get("transform")
        if transform_name and transform_name not in TRANSFORMS:
            raise SchemaValidationError(f"Invalid transform '{transform_name}' for col '{api_name}' in {filepath}")

    return schema

def validate_all_schemas(schemas_dir: str):
    validated = {}
    if not os.path.exists(schemas_dir):
        raise SchemaValidationError(f"Schemas directory not found: {schemas_dir}")

    for file in os.listdir(schemas_dir):
        if file.endswith(".json"):
            full_path = os.path.join(schemas_dir, file)
            schema = validate_schema_file(full_path)
            validated[schema["id"]] = schema
    return validated
