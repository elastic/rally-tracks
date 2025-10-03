import os

import yaml

filters = {}

# static file paths should be a comma-separated list of files or directories (omitting the trailing '/')
static_paths = os.environ.get("RUN_FULL_CI_WHEN_CHANGED", [])

# Statically include some files that should always trigger a full CI run
if static_paths:
    filters["full_ci"] = [f"{path}/**" if os.path.isdir(path.strip()) else path.strip() for path in static_paths.split(",")]

# Dynamically create filters for each track (top-level subdirectory) in the repo
for entry in os.listdir("."):
    if os.path.isdir(entry) and entry not in static_paths:
        filters[entry] = [f"{entry}/**"]


with open(".github/filters.yml", "w") as f:
    yaml.dump(filters, f, default_flow_style=False)
print(f"Created .github/filters.yml with {len(filters)} track(s): {', '.join(filters.keys())}")
