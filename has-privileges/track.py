import itertools
import random
import threading
import string
import bz2
import csv
import json
import os

from esrally import exceptions


KIBANA_APP_PRIVILEGES_FILENAME: str = "kibana-app-privileges.json.bz2"

def generate_random_name(length=10):
    return ''.join(random.choices(string.ascii_lowercase + string.digits + '_-', k=length))

def generate_random_index_expression(length=10):
    base = ''.join(random.choices(string.ascii_lowercase + string.digits + '_-', k=length))
    mode = random.choice(["prefix", "suffix", "both"])  # include 'none' to exclude adding wildcard

    if mode in ("prefix", "both"):
        base = "*" + base
    if mode in ("suffix", "both"):
        base = base + "*"

    return base

async def create_roles_and_users(es, params):
    # create 100 spaces
    spaces = []
    for i in range(100):
        spaces.append(f"space:space{i}")
    
    # create 1000 roles
    roles = []
    for i in range(1000):
        random_role_name = f"role_{i}"
        roles.append(random_role_name)

    for role_name in roles:
        indices_privileges = [
            {
                "names": [generate_random_index_expression()],
                "privileges": random.sample(["read", "write", "delete", "create"], k=2)
            } for _ in range(1)
        ]
        cluster_privileges = random.sample(["all", "monitor", "manage"], k=2)
        selected_spaces = random.sample(spaces, k=1)
        
        await es.security.put_role(
            name=role_name,
            indices=indices_privileges,
            cluster=cluster_privileges,
            applications=[
                {
                    "application": "kibana-.kibana",
                    "privileges": ["all"],
                    "resources": selected_spaces
                }
            ]
        )
    # create 100 users with subset of 300 roles
    for i in range(100):
        await es.security.put_user(
            username="user_" + str(i),
            password="password",
            roles=random.sample(roles, k=500)
        )

async def create_kibana_app_privileges(es, params):
    cwd = os.path.dirname(__file__)
    with bz2.open(os.path.join(cwd, KIBANA_APP_PRIVILEGES_FILENAME), "rt") as kibana_app_privileges_file:
        app_privileges = json.load(kibana_app_privileges_file)
        await es.security.put_privileges(
                body=app_privileges
        )

async def has_privileges(es, params):
    user_id = random.randint(1, 99)
    spaces = [f"space:space{i}" for i in random.sample(range(100), k=1)]
    await es.options(basic_auth=("user_" + str(user_id), "password")).security.has_privileges(
        body={
            "cluster": [
            "manage_security",
            "read_security",
            "manage_api_key",
            "manage_own_api_key",
            "cluster:admin/snapshot",
            "cluster:admin/repository",
            "manage",
            "manage_watcher",
            "monitor_watcher",
            "manage_pipeline",
            "cluster:monitor/nodes/info",
            "monitor_enrich",
            "manage_enrich",
            "manage_index_templates",
            "monitor",
            "manage_rollup",
            "manage_ccr",
            "manage_ilm",
            "read_ilm",
            "manage_logstash_pipelines",
            "monitor_transform"
            ],
            "index": [
            {
                "names": [
                ".watches"
                ],
                "privileges": [
                "read",
                "read"
                ]
            },
            {
                "names": [
                ".watcher-history-*"
                ],
                "privileges": [
                "read",
                "read"
                ]
            },
            {
                "names": [
                "logs-*-*"
                ],
                "privileges": [
                "read"
                ]
            },
            {
                "names": [
                "traces-*-*"
                ],
                "privileges": [
                "read"
                ]
            },
            {
                "names": [
                "metrics-*-*"
                ],
                "privileges": [
                "read"
                ]
            },
            {
                "names": [
                "synthetics-*-*"
                ],
                "privileges": [
                "read"
                ]
            }
            ],
            "application": [
            {
                "application": "kibana-.kibana",
                "resources": spaces,
                "privileges": [
                "login:",
                "ui:navLinks/error",
                "ui:navLinks/status",
                "ui:navLinks/r",
                "ui:navLinks/short_url_redirect",
                "ui:navLinks/kibana",
                "ui:navLinks/home",
                "ui:navLinks/management",
                "ui:navLinks/space_selector",
                "ui:navLinks/security_access_agreement",
                "ui:navLinks/security_capture_url",
                "ui:navLinks/security_login",
                "ui:navLinks/security_logout",
                "ui:navLinks/security_logged_out",
                "ui:navLinks/security_overwritten_session",
                "ui:navLinks/security_account",
                "ui:navLinks/graph",
                "ui:navLinks/kibanaOverview",
                "ui:navLinks/dev_tools",
                "ui:navLinks/searchSynonyms",
                "ui:navLinks/searchQueryRules",
                "ui:navLinks/visualize",
                "ui:navLinks/lens",
                "ui:navLinks/maps",
                "ui:navLinks/dashboards",
                "ui:navLinks/discover",
                "ui:navLinks/exploratory-view",
                "ui:navLinks/ml",
                "ui:navLinks/searchPlayground",
                "ui:navLinks/searchInferenceEndpoints",
                "ui:navLinks/integrations",
                "ui:navLinks/fleet",
                "ui:navLinks/ingestManager",
                "ui:navLinks/osquery",
                "ui:navLinks/securitySolutionUI",
                "ui:navLinks/siem",
                "ui:navLinks/enterpriseSearch",
                "ui:navLinks/enterpriseSearchContent",
                "ui:navLinks/enterpriseSearchElasticsearch",
                "ui:navLinks/enterpriseSearchVectorSearch",
                "ui:navLinks/enterpriseSearchSemanticSearch",
                "ui:navLinks/enterpriseSearchAISearch",
                "ui:navLinks/enterpriseSearchApplications",
                "ui:navLinks/enterpriseSearchAnalytics",
                "ui:navLinks/searchExperiences",
                "ui:navLinks/appSearch",
                "ui:navLinks/workplaceSearch",
                "ui:navLinks/enterpriseSearchRedirect",
                "ui:navLinks/observability-overview",
                "ui:navLinks/uptime",
                "ui:navLinks/slo",
                "ui:navLinks/synthetics",
                "ui:navLinks/observabilityAIAssistant",
                "ui:navLinks/observabilityOnboarding",
                "ui:navLinks/logs",
                "ui:navLinks/metrics",
                "ui:navLinks/apm",
                "ui:navLinks/ux",
                "ui:navLinks/streams",
                "ui:navLinks/observability-logs-explorer",
                "ui:navLinks/observability-log-explorer",
                "ui:navLinks/last-used-logs-viewer",
                "ui:navLinks/monitoring",
                "ui:navLinks/reportingRedirect",
                "ui:navLinks/canvas",
                "ui:management/insightsAndAlerting/triggersActions",
                "ui:management/insightsAndAlerting/triggersActionsConnectors",
                "ui:management/insightsAndAlerting/maintenanceWindows",
                "ui:management/insightsAndAlerting/cases",
                "ui:management/insightsAndAlerting/jobsListLink",
                "ui:management/insightsAndAlerting/watcher",
                "ui:management/insightsAndAlerting/reporting",
                "ui:management/kibana/tags",
                "ui:management/kibana/aiAssistantManagementSelection",
                "ui:management/kibana/securityAiAssistantManagement",
                "ui:management/kibana/observabilityAiAssistantManagement",
                "ui:management/kibana/search_sessions",
                "ui:management/kibana/settings",
                "ui:management/kibana/indexPatterns",
                "ui:management/kibana/filesManagement",
                "ui:management/kibana/objects",
                "ui:management/kibana/spaces",
                "ui:management/security/users",
                "ui:management/security/roles",
                "ui:management/security/api_keys",
                "ui:management/security/role_mappings",
                "ui:management/data/snapshot_restore",
                "ui:management/data/migrate_data",
                "ui:management/data/rollup_jobs",
                "ui:management/data/remote_clusters",
                "ui:management/data/cross_cluster_replication",
                "ui:management/data/index_lifecycle_management",
                "ui:management/data/data_quality",
                "ui:management/data/transform",
                "ui:management/stack/license_management",
                "ui:management/stack/upgrade_assistant",
                "ui:management/ingest/ingest_pipelines",
                "ui:management/ingest/pipelines",
                "ui:catalogue/observabilityAIAssistant",
                "ui:catalogue/graph",
                "ui:catalogue/searchSynonyms",
                "ui:catalogue/searchQueryRules",
                "ui:catalogue/maps",
                "ui:catalogue/ml",
                "ui:catalogue/ml_file_data_visualizer",
                "ui:catalogue/searchPlayground",
                "ui:catalogue/searchInferenceEndpoints",
                "ui:catalogue/fleet",
                "ui:catalogue/osquery",
                "ui:catalogue/securitySolution",
                "ui:catalogue/enterpriseSearch",
                "ui:catalogue/enterpriseSearchContent",
                "ui:catalogue/enterpriseSearchElasticsearch",
                "ui:catalogue/appSearch",
                "ui:catalogue/workplaceSearch",
                "ui:catalogue/searchExperiences",
                "ui:catalogue/enterpriseSearchVectorSearch",
                "ui:catalogue/enterpriseSearchSemanticSearch",
                "ui:catalogue/enterpriseSearchAISearch",
                "ui:catalogue/enterpriseSearchApplications",
                "ui:catalogue/enterpriseSearchAnalytics",
                "ui:catalogue/observability",
                "ui:catalogue/slo",
                "ui:catalogue/uptime",
                "ui:catalogue/infraops",
                "ui:catalogue/metrics",
                "ui:catalogue/infralogging",
                "ui:catalogue/logs",
                "ui:catalogue/apm",
                "ui:catalogue/monitoring",
                "ui:catalogue/canvas",
                "ui:catalogue/discover",
                "ui:catalogue/visualize",
                "ui:catalogue/dashboard",
                "ui:catalogue/console",
                "ui:catalogue/searchprofiler",
                "ui:catalogue/grokdebugger",
                "ui:catalogue/advanced_settings",
                "ui:catalogue/indexPatterns",
                "ui:catalogue/saved_objects",
                "ui:catalogue/security",
                "ui:catalogue/snapshot_restore",
                "ui:catalogue/watcher",
                "ui:catalogue/rollup_jobs",
                "ui:catalogue/index_lifecycle_management",
                "ui:catalogue/reporting",
                "ui:catalogue/transform",
                "ui:catalogue/spaces",
                "ui:savedQueryManagement/saveQuery",
                "ui:savedObjectsManagement/read",
                "ui:savedObjectsManagement/edit",
                "ui:savedObjectsManagement/delete",
                "ui:savedObjectsManagement/copyIntoSpace",
                "ui:savedObjectsManagement/shareIntoSpace",
                "ui:indexPatterns/save",
                "ui:advancedSettings/save",
                "ui:advancedSettings/show",
                "ui:dev_tools/show",
                "ui:dev_tools/save",
                "ui:dashboard/createNew",
                "ui:dashboard/show",
                "ui:dashboard/showWriteControls",
                "ui:dashboard/saveQuery",
                "ui:dashboard/createShortUrl",
                "ui:dashboard/storeSearchSession",
                "ui:visualize/show",
                "ui:visualize/delete",
                "ui:visualize/save",
                "ui:visualize/saveQuery",
                "ui:visualize/createShortUrl",
                "ui:discover/show",
                "ui:discover/save",
                "ui:discover/saveQuery",
                "ui:discover/createShortUrl",
                "ui:discover/storeSearchSession",
                "ui:canvas/save",
                "ui:canvas/show",
                "ui:manageReporting/show",
                "ui:dataQuality/show",
                "ui:dataQuality/alerting:save",
                "ui:apm/show",
                "ui:apm/save",
                "ui:apm/alerting:show",
                "ui:apm/alerting:save",
                "ui:apm/settings:save",
                "ui:logs/show",
                "ui:logs/configureSource",
                "ui:logs/save",
                "ui:infrastructure/show",
                "ui:infrastructure/configureSource",
                "ui:infrastructure/save",
                "ui:uptime/save",
                "ui:uptime/configureSettings",
                "ui:uptime/show",
                "ui:uptime/alerting:save",
                "ui:uptime/elasticManagedLocationsEnabled",
                "ui:uptime/canManagePrivateLocations",
                "ui:slo/read",
                "ui:slo/write",
                "ui:observabilityCasesV3/create_cases",
                "ui:observabilityCasesV3/read_cases",
                "ui:observabilityCasesV3/update_cases",
                "ui:observabilityCasesV3/push_cases",
                "ui:observabilityCasesV3/cases_connectors",
                "ui:observabilityCasesV3/delete_cases",
                "ui:observabilityCasesV3/cases_settings",
                "ui:observabilityCasesV3/create_comment",
                "ui:observabilityCasesV3/case_reopen",
                "ui:observabilityCasesV3/cases_assign",
                "ui:securitySolutionSiemMigrations/all",
                "ui:securitySolutionNotes/read",
                "ui:securitySolutionNotes/crud",
                "ui:securitySolutionTimeline/read",
                "ui:securitySolutionTimeline/crud",
                "ui:securitySolutionAttackDiscovery/attack-discovery",
                "ui:securitySolutionAssistant/ai-assistant",
                "ui:securitySolutionAssistant/updateAIAssistantAnonymization",
                "ui:securitySolutionAssistant/manageGlobalKnowledgeBaseAIAssistant",
                "ui:securitySolutionCasesV3/create_cases",
                "ui:securitySolutionCasesV3/read_cases",
                "ui:securitySolutionCasesV3/update_cases",
                "ui:securitySolutionCasesV3/push_cases",
                "ui:securitySolutionCasesV3/cases_connectors",
                "ui:securitySolutionCasesV3/delete_cases",
                "ui:securitySolutionCasesV3/cases_settings",
                "ui:securitySolutionCasesV3/create_comment",
                "ui:securitySolutionCasesV3/case_reopen",
                "ui:securitySolutionCasesV3/cases_assign",
                "ui:siemV2/show",
                "ui:siemV2/crud",
                "ui:siemV2/entity-analytics",
                "ui:siemV2/detections",
                "ui:siemV2/investigation-guide",
                "ui:siemV2/investigation-guide-interactions",
                "ui:siemV2/threat-intelligence",
                "ui:siemV2/showEndpointExceptions",
                "ui:siemV2/crudEndpointExceptions",
                "ui:siemV2/writeEndpointList",
                "ui:siemV2/readEndpointList",
                "ui:siemV2/writeTrustedApplications",
                "ui:siemV2/readTrustedApplications",
                "ui:siemV2/readHostIsolationExceptions",
                "ui:siemV2/deleteHostIsolationExceptions",
                "ui:siemV2/accessHostIsolationExceptions",
                "ui:siemV2/writeHostIsolationExceptions",
                "ui:siemV2/writeBlocklist",
                "ui:siemV2/readBlocklist",
                "ui:siemV2/writeEventFilters",
                "ui:siemV2/readEventFilters",
                "ui:siemV2/writePolicyManagement",
                "ui:siemV2/readPolicyManagement",
                "ui:siemV2/writeActionsLogManagement",
                "ui:siemV2/readActionsLogManagement",
                "ui:siemV2/writeHostIsolationRelease",
                "ui:siemV2/writeHostIsolation",
                "ui:siemV2/writeProcessOperations",
                "ui:siemV2/writeFileOperations",
                "ui:siemV2/writeExecuteOperations",
                "ui:siemV2/writeScanOperations",
                "ui:osquery/read",
                "ui:osquery/write",
                "ui:osquery/writeLiveQueries",
                "ui:osquery/readLiveQueries",
                "ui:osquery/runSavedQueries",
                "ui:osquery/writeSavedQueries",
                "ui:osquery/readSavedQueries",
                "ui:osquery/writePacks",
                "ui:osquery/readPacks",
                "ui:fleet/read",
                "ui:fleet/all",
                "ui:fleetv2/read",
                "ui:fleetv2/all",
                "ui:fleetv2/agents_read",
                "ui:fleetv2/agents_all",
                "ui:fleetv2/agent_policies_read",
                "ui:fleetv2/agent_policies_all",
                "ui:fleetv2/settings_read",
                "ui:fleetv2/settings_all",
                "ui:ml/isADEnabled",
                "ui:ml/isDFAEnabled",
                "ui:ml/isNLPEnabled",
                "ui:ml/canCreateJob",
                "ui:ml/canDeleteJob",
                "ui:ml/canOpenJob",
                "ui:ml/canCloseJob",
                "ui:ml/canResetJob",
                "ui:ml/canUpdateJob",
                "ui:ml/canForecastJob",
                "ui:ml/canDeleteForecast",
                "ui:ml/canCreateDatafeed",
                "ui:ml/canDeleteDatafeed",
                "ui:ml/canStartStopDatafeed",
                "ui:ml/canUpdateDatafeed",
                "ui:ml/canPreviewDatafeed",
                "ui:ml/canGetFilters",
                "ui:ml/canCreateCalendar",
                "ui:ml/canDeleteCalendar",
                "ui:ml/canCreateFilter",
                "ui:ml/canDeleteFilter",
                "ui:ml/canCreateDataFrameAnalytics",
                "ui:ml/canDeleteDataFrameAnalytics",
                "ui:ml/canStartStopDataFrameAnalytics",
                "ui:ml/canCreateMlAlerts",
                "ui:ml/canUseMlAlerts",
                "ui:ml/canViewMlNodes",
                "ui:ml/canCreateTrainedModels",
                "ui:ml/canDeleteTrainedModels",
                "ui:ml/canStartStopTrainedModels",
                "ui:ml/canCreateInferenceEndpoint",
                "ui:ml/canGetJobs",
                "ui:ml/canGetDatafeeds",
                "ui:ml/canGetCalendars",
                "ui:ml/canFindFileStructure",
                "ui:ml/canGetDataFrameAnalytics",
                "ui:ml/canGetAnnotations",
                "ui:ml/canCreateAnnotation",
                "ui:ml/canDeleteAnnotation",
                "ui:ml/canGetTrainedModels",
                "ui:ml/canTestTrainedModels",
                "ui:ml/canGetFieldInfo",
                "ui:ml/canGetMlInfo",
                "ui:ml/canUseAiops",
                "ui:generalCasesV3/create_cases",
                "ui:generalCasesV3/read_cases",
                "ui:generalCasesV3/update_cases",
                "ui:generalCasesV3/push_cases",
                "ui:generalCasesV3/cases_connectors",
                "ui:generalCasesV3/delete_cases",
                "ui:generalCasesV3/cases_settings",
                "ui:generalCasesV3/create_comment",
                "ui:generalCasesV3/case_reopen",
                "ui:generalCasesV3/cases_assign",
                "ui:streams/show",
                "ui:streams/manage",
                "ui:maps/save",
                "ui:maps/show",
                "ui:maps/saveQuery",
                "ui:searchQueryRules/manage",
                "ui:searchSynonyms/manage",
                "ui:maintenanceWindow/show",
                "ui:maintenanceWindow/save",
                "ui:rulesSettings/show",
                "ui:rulesSettings/save",
                "ui:rulesSettings/writeFlappingSettingsUI",
                "ui:rulesSettings/readFlappingSettingsUI",
                "ui:rulesSettings/writeAlertDeleteSettingsUI",
                "ui:rulesSettings/readAlertDeleteSettingsUI",
                "ui:graph/save",
                "ui:graph/delete",
                "ui:graph/show",
                "ui:savedObjectsTagging/view",
                "ui:savedObjectsTagging/create",
                "ui:savedObjectsTagging/edit",
                "ui:savedObjectsTagging/delete",
                "ui:savedObjectsTagging/assign",
                "ui:observabilityAIAssistant/show",
                "ui:actions/show",
                "ui:actions/execute",
                "ui:actions/save",
                "ui:actions/delete",
                "ui:actions/endpointSecurityExecute",
                "ui:guidedOnboardingFeature/enabled",
                "ui:spaces/manage",
                "ui:globalSettings/show",
                "ui:globalSettings/save",
                "ui:fileUpload/show",
                "ui:aiops/enabled"
                ]
            }
            ]
        }
    )

def register(registry):
    registry.register_runner("create-roles-and-users", create_roles_and_users, async_runner=True)
    registry.register_runner("create-kibana-app-privileges", create_kibana_app_privileges, async_runner=True)
    registry.register_runner("has-privileges", has_privileges, async_runner=True)
