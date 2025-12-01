# Has-Privileges Track

Benchmarks the Elasticsearch `_has_privileges` API with configurable scale and wildcard patterns for index privileges and Kibana application privileges.

## Overview

This track simulates realistic authorization checking scenarios by:
1. Creating a configurable number of roles
2. Creating users assigned to a subset of those roles
3. Loading Kibana application privileges for a specific Kibana version
4. Benchmarking the `_has_privileges` API performance under various conditions

## Prerequisites

**Security must be enabled** in your Elasticsearch cluster. This track requires:
- X-Pack Security enabled
- A superuser with privileges to create roles, users, and call the `_has_privileges` API. We use the provided `rally` user for this purpose. Note that when running this track on esbench, that tooling injects its own superuser as an override.

## Available Parameters

All parameters can be configured via `--track-params` when running Rally:

| Parameter | Type    | Default | Description                                                                             |
|-----------|---------|---------|-----------------------------------------------------------------------------------------|
| `num_roles` | integer | 1000 | Total number of roles to create                                                         |
| `num_users` | integer | 100 | Total number of users to create                                                         |
| `num_roles_per_user` | integer | 300 | Number of roles assigned to each user. Note: `num_roles_per_user` must be ≤ `num_roles` |
| `num_spaces` | integer | 100 | Number of Kibana spaces to create                                                       |
| `wildcard_mode` | both    | "mixed" | Wildcard pattern mode (see below)                                                       |
| `kibana_privileges_as_of` | string  | "8.19.7" | Kibana version for application privileges                                               |
| `iterations` | integer | 10 | Number of benchmark iterations                                                          |
| `clients` | integer | 5 | Number of concurrent clients                                                            |
| `warmup_iterations` | integer | (optional) | Number of warmup iterations before benchmark                                            |

### Wildcard Modes

The `wildcard_mode` parameter controls how index patterns are generated:

| Mode | Pattern Example | Description |
|------|-----------------|-------------|
| `both` | `*index*` | Both prefix and suffix wildcards |
| `prefix` | `*index` | Prefix wildcard only |
| `suffix` | `index*` | Suffix wildcard only |
| `none` | `index` | No wildcards |
| `mixed` | Random | Randomly chooses one of the above modes per index |

## Usage Examples

### Running with Rally-Provisioned Cluster

Use the built-in `x-pack-security` car mixin. Note that `track-path` is relative to current working directory and you may need to fiddle with it to point it to the correct location for your track's `track.json` config.

#### Small Scale - Both Wildcards - Kibana 8.x
```bash
esrally race --track-path=has_privileges \
  --car="4gheap,x-pack-security" \
  --client-options="use_ssl:true,verify_certs:false,basic_auth_user:'rally',basic_auth_password:'rally-password'" \
  --track-params="num_roles:10,num_users:10,num_roles_per_user:5,num_spaces:10,wildcard_mode:both,kibana_privileges_as_of:8.19.7,iterations:10,clients:5"
```

#### Medium Scale - No Wildcards - Kibana 8.x
```bash
esrally race --track-path=has_privileges \
  --car="4gheap,x-pack-security" \
  --client-options="use_ssl:true,verify_certs:false,basic_auth_user:'rally',basic_auth_password:'rally-password'" \
  --track-params="num_roles:100,num_users:50,num_roles_per_user:30,num_spaces:50,wildcard_mode:none,kibana_privileges_as_of:8.19.7,iterations:10,clients:5"
```

#### Stress Test - High Concurrency with Warmup
```bash
esrally race --track-path=has_privileges \
  --car="4gheap,x-pack-security" \
  --client-options="use_ssl:true,verify_certs:false,basic_auth_user:'rally',basic_auth_password:'rally-password'" \
  --track-params="num_roles:1000,num_users:200,num_roles_per_user:500,num_spaces:150,wildcard_mode:both,kibana_privileges_as_of:9.2.1,iterations:100,clients:20,warmup_iterations:10"
```

## Benchmark Workflow

The track executes the following operations in order:

1. **Create Roles and Users** (`create_roles_and_users`)
   - Creates `num_roles` roles with random index patterns
   - Each role has random index privileges (read, write, delete, create)
   - Each role has random cluster privileges (all, monitor, manage)
   - Each role has Kibana application privileges for random spaces
   - Creates `num_users` users, each assigned `num_roles_per_user` random roles

2. **Create Kibana Application Privileges** (`create_kibana_app_privileges`)
   - Loads version-specific Kibana application privileges

3. **Benchmark _has_privileges API** (`has-privileges`)
   - Randomly selects a user from the created users
   - Calls `_has_privileges` API checking cluster, index, and application privileges
   - Repeats for the specified number of iterations with concurrent clients

## Track Processor

This track uses a custom track processor (`HasPrivilegesDataDownloader`) to automate the download of required data files before the benchmark runs. Track processors in Rally enable pre-flight activities by implementing lifecycle methods that execute before benchmark operations begin.

### What It Does

The track processor handles two types of downloads during the track preparation phase:

1. **Request Body Template** (`has-privileges-request-body.json`)
   - Downloaded from: `https://rally-tracks.elastic.co/has-privileges/has-privileges-request-body.json`
   - Contains the Jinja2 template for the `_has_privileges` API request
   - Used during benchmark execution to generate requests with randomized Kibana spaces

2. **Kibana Application Privileges** (`kibana-app-privileges-{version}.json.bz2`)
   - Downloaded based on the `version` parameter (e.g., `8.19.7` or `9.2.1`)
   - Contains version-specific Kibana application privilege definitions
   - Loaded into Elasticsearch during the `create_kibana_app_privileges` setup operation

### How It Works

The track processor uses the `on_prepare_track` lifecycle method, which executes after Rally loads the track but before any benchmark operations run. This method:

1. Reads the `version` parameter from the challenge configuration
2. Downloads files to `~/.rally/benchmarks/data/has_privileges/`
3. Skips downloads if files already exist (for faster subsequent runs)

Files are downloaded once during track preparation and reused across all benchmark iterations. If you need to force a re-download, delete the files from the data directory.

### Implementation

The track processor is registered in `track.py`:

```python
def register(registry):
    registry.register_track_processor(HasPrivilegesDataDownloader())
    # ... register runners
```
For more information about track processors, see the Rally documentation: [Manipulating track objects and data with track processors](https://esrally.readthedocs.io/en/stable/advanced.html#manipulating-track-objects-and-data-with-track-processors)

## Supported Kibana Versions

The track includes application privilege definitions for:
- Kibana 8.x (8.19.7)
- Kibana 9.x (9.2.1)

To use a different version, specify it via `version` parameter. The track will attempt to load `kibana-app-privileges-{version}.json.bz2`.

These files have been uploaded to:
- https://rally-tracks.elastic.co/has-privileges/kibana-app-privileges-8.19.7.json.bz2
- https://rally-tracks.elastic.co/has-privileges/kibana-app-privileges-9.2.1.json.bz2

Till such a time that we can fully automate this process, Elasticsearch engineering should occasionally extract the application privileges of newer versions of Kibana and update them at this location. Rally was intended to be a tool for benchmarking Elasticsearch and it isn't capable of bringing up a Kibana instance which would be needed for such an automation. So, Rally will likely not be not enough for whatever the eventual solution is. We would need to script a preliminary step using esbench potentially. Further research on this is needed.

Current process: turn on Kibana + ES (easiest to use standard docker images) and wait for Kibana to become available. When first turned on, Kibana bootstraps its application privilege model into the ES security index. Once Kibana is ready, we can hit the ES endpoint `GET /_security/privilege` with superuser access to retrieve the privileges JSON and download it. Use `bzip2 -k {file}.json` to compress and then upload. 

### Further Reading
https://esrally.readthedocs.io/en/stable/adding_tracks.html
https://esrally.readthedocs.io/en/stable/car.html
https://esrally.readthedocs.io/en/stable/command_line_reference.html
