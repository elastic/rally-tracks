# Licensed to Elasticsearch B.V. under one or more contributor
# license agreements. See the NOTICE file distributed with
# this work for additional information regarding copyright
# ownership. Elasticsearch B.V. licenses this file to you under
# the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.


async def validate_package_assets(es, params):
    packages = params.get("packages", [])
    asset_types = params.get("asset-types", [])

    if "index-templates" in asset_types:
        all_templates = await es.indices.get_index_template()
        package_templates = []

        for template in all_templates["index_templates"]:
            meta = template["index_template"].get("_meta")
            if meta is not None:
                package = meta.get("package", None)
                if package is not None:
                    package_templates.append(package["name"])

        if missing_templates := [p for p in packages if p not in package_templates]:
            raise BaseException(f"Index templates missing for packages: {sorted(missing_templates)}")
        else:
            return True
