import os

import yaml

filters = {}
for entry in os.listdir("."):
    if os.path.isdir(entry):
        filters[entry] = [f"{entry}/**"]
with open(".github/filters.yml", "w") as f:
    yaml.dump(filters, f, default_flow_style=False)
print(f"Created .github/filters.yml with {len(filters)} track(s): {', '.join(filters.keys())}")
