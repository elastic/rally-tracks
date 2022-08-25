#!/usr/bin/env python3

####################################################################
#
# anonymize a metricbeat dump
#
####################################################################
#
# This is a strange balance of openness and paranoia. And all hacky.
# When we see a field or log pattern we don't recognize we fail the
# processing entirely and raise an error. So that a human can look at
# the new thing and decide if it should be changed. We're fairly
# willing to leave things, though we consume the bodies of many log
# messages and replace uuids and host names and ips and application
# names. But we let metric values pass right through. We need to let
# them through because TSDB is optimized for real world data.
#
####################################################################


import ipaddress
import json
import sys
import uuid


def passthrough(v):
    return v


def numbered(prefix):
    numbers = {}

    def number_it(v):
        if v not in numbers:
            numbers[v] = len(numbers)
        return f"{prefix}{numbers[v]}"

    return number_it


def uids():
    uids = {}

    def replace_uid(v):
        if v not in uids:
            uids[v] = uuid.uuid4()
        return str(uids[v])

    return replace_uid


def ips():
    ips = {}

    def replace_ip(v):
        if v not in ips:
            ips[v] = ipaddress.IPv4Address(len(ips))
        return str(ips[v])

    return replace_ip


def container_runtime(v):
    if v == "docker":
        return v
    raise ValueError(f"unexpected service address [{v}]")


def service_type(v):
    if v == "kubernetes":
        return v
    raise ValueError(f"unexepected service type [{v}]")


container_ids = {}


def container_id(id):
    if id not in container_ids:
        container_ids[id] = uuid.uuid4()
    return str(container_ids[id])


def k8s_container_id(id):
    if id.startswith("docker://"):
        return "docker://" + container_id(id[len("docker://") :])
    raise ValueError(f"unexepected k8s container prefix [{id}]")


K8S_IMAGE_PASSTHROUGH = {
    "centos:7",
    "gcr.io/cloud-builders/gsutil:latest",
    "nginx:stable",
}
k8s_images_docker_es_co = numbered("docker.elastic.co/image-name-")
k8s_images_elastic = numbered("elastic/image-name-")
k8s_images_gradle = numbered("registry.replicated.com/gradleenterprise/image-name-")
k8s_images_other = numbered("anon/image-")


def k8s_container_image(img):
    if img in K8S_IMAGE_PASSTHROUGH:
        return img
    if img.startswith("sha256:"):
        return img
    if img.startswith("docker.elastic.co/"):
        return k8s_images_docker_es_co(img[len("docker.elastic.co/") :])
    if img.startswith("elastic/"):
        return k8s_images_docker_es_co(img[len("elastic/") :])
    if img.startswith("registry.replicated.com/gradleenterprise/"):
        return k8s_images_gradle(img[len("registry.replicated.com/gradleenterprise/") :])
    if "elastic" in img:
        raise ValueError(f"unexpected k8s container image [{img}]")
    return k8s_images_other(img)


K8S_MESSAGE_PASSTHROUGH = {
    "Back-off restarting failed container",
    'Container image "centos:7" already present on machine',
    "Created container check",
    "deleting pod for node scale down",
    "Error: ImagePullBackOff",
    "Job has reached the specified backoff limit",
    "Job was active longer than specified deadline",
    "marked the node as toBeDeleted/unschedulable",
    "No matching pods found",
    "node removed by cluster autoscaler",
    "Pod sandbox changed, it will be killed and re-created.",
    "Pod was evicted by VPA Updater to apply resource recommendation.",
    "Started container check",
    "Starting kubelet.",
    "Starting kube-proxy.",
    "Too many active pods running after completion count reached",
    "Updated load balancer with new hosts",
    "Updated Node Allocatable limit across pods",
}
K8S_MESSAGE_SNIP = {
    "event: Deleting": "Deleting node <snip>",
    "event: Removing Node": "Removing node <snip>",
    "event: Registered Node": "registered node <snip>",
    "Created pod: ": "Create pod <snip>",
    "Successfully assigned": "Successfully assigned <snip>",
    "Created job": "Created job <snip>",
    "Scaled up replica set": "Scaled up replica set",
    "Pulling image": "Pulling image <snip>",
    "Started container": "Started container <snip>",
    "Successfully pulled image": "Successfully pulled image <snip>",
    "Created container": "Created container <snip>",
    "Cannot determine if job needs to be started": "Cannot determine if job needs to be started <snip>",
    "Saw completed job": "Saw completed job <snip>",
    "Deleted job": "Deleted job <snip>",
    "AttachVolume.Attach succeeded for volume": "AttachVolume.Attach succeeded for volume <snip>",
    "Scaled down replica set": "Scaled down replica set <snip>",
    "Stopping container": "Stopping container <snip>",
    "Deleted pod": "Deleted pod <snip>",
    "Back-off pulling image": "Back-off pulling image <snip>",
    "Liveness probe failed": "Liveness probe failed <snip>",
    "delete Pod": "Delete pod <snip>",
    "create Pod": "Create pod <snip>",
    "status is now: NodeNotReady": "Node not ready <snip>",
    "Readiness probe failed": "Readiness probe failed <snip>",
    "Readiness probe errored": "Readiness probe errored <snip>",
    "nodes are available:": "Bad nodes <snip>",
    "Saw a job that the controller did not create or forgot": "Saw a job that the controller did not create or forgot <snip>",
    "or sacrifice child": "Brutal murder by oomkiller",
    "Scale-up": "Scale-up <snip>",
    "Scale-down": "Scale-down <snip>",
    "status is now": "<snip> status change <snip>",
    "failed for volume": "<snip> failed for volume <snip>",
    "pod triggered scale-up": "pod triggered scale-up <snip>",
    "Unable to mount volumes for pod": "Unable to mount volumes for pod <snip>",
    "Volume is already exclusively attached to one node": "Volume is already exclusively attached to one node <snip>",
    "failed liveness probe, will be restarted": "<snip> failed liveness probe, will be restarted",
    "Failed create pod sandbox": "Failed create pod sandbox <snip>",
    "Error: cannot find volume": "Error: cannot find volume <snip>",
    "Couldn't find key user in": "Couldn't find key user in <snip>",
}


def k8s_message(message):
    if message in K8S_MESSAGE_PASSTHROUGH:
        return message
    if "Error: secret" in message and "not found" in message:
        return "Error: secret <snip> not found"
    if "Container image " in message and "already present on machine" in message:
        return "Container image <snip> already present on machine"
    if '"unmanaged"' in message:
        return str(uuid.uuid4())
    for trigger, replacement in K8S_MESSAGE_SNIP.items():
        if trigger in message:
            return replacement
    raise ValueError(f"unsupported k8s.event.message [{message}]")


def k8s_event_generate_name(v):
    if v == "":
        return v
    raise ValueError(f"unsupported k8s.event.generate_name [{v}]")


PASSTHROUGH_REASONS = {
    "BackOff",
    "BackoffLimitExceeded",
    "CIDRAssignmentFailed",
    "Created",
    "DeadlineExceeded",
    "EvictedByVPA",
    "Failed",
    "FailedAttachVolume",
    "FailedCreatePodSandBox",
    "FailedMount",
    "FailedNeedsStart",
    "FailedScheduling",
    "Killing",
    "NodeAllocatableEnforced",
    "NodeHasNoDiskPressure",
    "NodeHasSufficientMemory",
    "NodeHasSufficientPID",
    "NodeNotReady",
    "NodeReady",
    "NodeSysctlChange",
    "NoPods",
    None,
    "OOMKilling",
    "Pulled",
    "Pulling",
    "RegisteredNode",
    "RemovingNode",
    "SandboxChanged",
    "SawCompletedJob",
    "ScaleDown",
    "ScaleDownEmpty",
    "ScaledUpGroup",
    "ScalingReplicaSet",
    "Scheduled",
    "Started",
    "Starting",
    "SuccessfulAttachVolume",
    "SuccessfulCreate",
    "SuccessfulDelete",
    "TooManyActivePods",
    "TriggeredScaleUp",
    "UnexpectedJob",
    "Unhealthy",
    "UpdatedLoadBalancer",
}


def k8s_event_reason(v):
    if v in PASSTHROUGH_REASONS:
        return v
    if "because it does not exist in the cloud provider" in v:
        return "Deleting <snip> because it does not exist in the cloud provider"
    raise ValueError(f"unsupported k8s.event.reason [{v}]")


def k8s_event_type(v):
    if v in {"Normal", "Warning"}:
        return v
    raise ValueError(f"unsupported k8s.event.type [{v}]")


def k8s_system_container(v):
    if v in {"kubelet", "pods", "runtime"}:
        return v
    raise ValueError(f"unsupported k8s.system.container [{v}]")


def k8s_labels_heritage(v):
    if v in {"Helm", "Tiller"}:
        return v
    raise ValueError(f"unsupported k8s.labels.heritage [{v}]")


K8S_LABELS_K8S_APP_PASSTHROUGH = {
    "dashboard-metrics-scraper",
    "glbc",
    "kubernetes-dashboard",
    "kube-dns",
    "kube-dns-autoscaler",
    "metrics-server",
}


def k8s_labels_k8s_app(v):
    if v in K8S_LABELS_K8S_APP_PASSTHROUGH:
        return v
    raise ValueError(f"unsupported k8s.labels.k8s-app [{v}]")


def k8s_labels_k8s_arch(v):
    if v == "amd64":
        return v
    raise ValueError(f"unsupported kubernetes.labels.kubernetes_io/arch [{v}]")


def k8s_labels_k8s_os(v):
    if v == "linux":
        return v
    raise ValueError(f"unsupported kubernetes.labels.kubernetes_io/os [{v}]")


def k8s_pod_status_phase(v):
    if v in {"failed", "pending", "running", "succeeded"}:
        return v
    raise ValueError(f"unsupported kubernetes.pod.status.phase [{v}]")


k8s_labels_names = numbered("k8s-labels-name-")


def k8s_labels_name(v):
    if v in {"glbc", "tiller"}:
        return v
    if v == "export-workday-logs-hourly":
        return k8s_labels_names(v)
    raise ValueError(f"unsupported kubernetes.labels.name [{v}]")


def k8s_labels_app_managed_by(v):
    if v == "Tiller":
        return v
    raise ValueError(f"unsupported kubernetes.labels.app_kubernetes_io/managed-by [{v}]")


K8S_CONTAINER_STATUS_REASON = {
    "Completed",
    "ContainerCreating",
    "CrashLoopBackOff",
    "CreateContainerConfigError",
    "ErrImagePull",
    "Error",
    "ImagePullBackOff",
    "OOMKilled",
}


def k8s_container_status_reason(v):
    if v in K8S_CONTAINER_STATUS_REASON:
        return v
    raise ValueError(f"unsupported k8s.container.status.reason [{v}]")


def metricbeat_error_message(message):
    if "error doing HTTP request to fetch" in message and "Metricset data" in message:
        return "Error fetching metrics <snip>"
    if "decoding of metric family failed" in message:
        return "Error fetching metrics <snip>"
    raise ValueError(f"unsupported error.message [{message}]")


strategies = {
    "@timestamp": passthrough,
    "agent.ephemeral_id": uids(),
    "agent.hostname": numbered("gke-apps-host-name-"),
    "agent.id": uids(),
    "agent.type": passthrough,
    "agent.version": passthrough,
    "container.id": container_id,
    "container.runtime": container_runtime,
    "ecs.version": passthrough,
    "error.message": metricbeat_error_message,
    "event.dataset": passthrough,
    "event.duration": passthrough,
    "event.module": passthrough,
    "fields.cluster": passthrough,
    "host.name": numbered("gke-apps-host-name-"),
    "kubernetes.container.cpu.limit.cores": passthrough,
    "kubernetes.container.cpu.request.cores": passthrough,
    "kubernetes.container.cpu.usage.core.ns": passthrough,
    "kubernetes.container.cpu.usage.limit.pct": passthrough,
    "kubernetes.container.cpu.usage.nanocores": passthrough,
    "kubernetes.container.cpu.usage.node.pct": passthrough,
    "kubernetes.container.id": k8s_container_id,
    "kubernetes.container.image": k8s_container_image,
    "kubernetes.container.logs.available.bytes": passthrough,
    "kubernetes.container.logs.capacity.bytes": passthrough,
    "kubernetes.container.logs.inodes.count": passthrough,
    "kubernetes.container.logs.inodes.free": passthrough,
    "kubernetes.container.logs.inodes.used": passthrough,
    "kubernetes.container.logs.used.bytes": passthrough,
    "kubernetes.container.memory.available.bytes": passthrough,
    "kubernetes.container.memory.majorpagefaults": passthrough,
    "kubernetes.container.memory.limit.bytes": passthrough,
    "kubernetes.container.memory.pagefaults": passthrough,
    "kubernetes.container.memory.request.bytes": passthrough,
    "kubernetes.container.memory.rss.bytes": passthrough,
    "kubernetes.container.memory.usage.bytes": passthrough,
    "kubernetes.container.memory.usage.limit.pct": passthrough,
    "kubernetes.container.memory.usage.node.pct": passthrough,
    "kubernetes.container.memory.workingset.bytes": passthrough,
    "kubernetes.container.name": numbered("container-name-"),
    "kubernetes.container.rootfs.available.bytes": passthrough,
    "kubernetes.container.rootfs.capacity.bytes": passthrough,
    "kubernetes.container.rootfs.inodes.used": passthrough,
    "kubernetes.container.rootfs.used.bytes": passthrough,
    "kubernetes.container.start_time": passthrough,
    "kubernetes.container.status.phase": passthrough,
    "kubernetes.container.status.ready": passthrough,
    "kubernetes.container.status.reason": k8s_container_status_reason,
    "kubernetes.container.status.restarts": passthrough,
    "kubernetes.event.count": passthrough,
    "kubernetes.event.involved_object.api_version": passthrough,
    "kubernetes.event.involved_object.kind": passthrough,
    "kubernetes.event.involved_object.name": numbered("involved-object-name-"),
    "kubernetes.event.involved_object.resource_version": passthrough,
    "kubernetes.event.involved_object.uid": uids(),
    "kubernetes.event.message": k8s_message,
    "kubernetes.event.metadata.generate_name": k8s_event_generate_name,
    "kubernetes.event.metadata.name": numbered("event-metadata-name-"),
    "kubernetes.event.metadata.namespace": numbered("event-metadata-namespace-"),
    "kubernetes.event.metadata.resource_version": passthrough,
    "kubernetes.event.metadata.self_link": numbered("event-metadata-self-link-"),
    "kubernetes.event.metadata.timestamp.created": passthrough,
    "kubernetes.event.metadata.uid": uids(),
    "kubernetes.event.reason": k8s_event_reason,
    "kubernetes.event.timestamp.first_occurrence": passthrough,
    "kubernetes.event.timestamp.last_occurrence": passthrough,
    "kubernetes.event.type": k8s_event_type,
    "kubernetes.labels.app": numbered("label-app-"),
    "kubernetes.labels.app_kubernetes_io/component": numbered("app_kubernetes_io/component-"),
    "kubernetes.labels.app_kubernetes_io/instance": numbered("app_kubernetes_io/instance-"),
    "kubernetes.labels.app_kubernetes_io/managed-by": k8s_labels_app_managed_by,
    "kubernetes.labels.app_kubernetes_io/name": numbered("app_kubernetes_io/name-"),
    "kubernetes.labels.beta_kubernetes_io/arch": k8s_labels_k8s_arch,
    "kubernetes.labels.beta_kubernetes_io/fluentd-ds-ready": "drop",
    "kubernetes.labels.beta_kubernetes_io/instance-type": numbered("beta_kubernetes_io/instance-type-"),
    "kubernetes.labels.beta_kubernetes_io/os": k8s_labels_k8s_os,
    "kubernetes.labels.chart": numbered("chart-"),
    "kubernetes.labels.cloud_google_com/gke-nodepool": "drop",
    "kubernetes.labels.cloud_google_com/gke-os-distribution": "drop",
    "kubernetes.labels.co_elastic_apps_oblt-test-plans_service": "drop",
    "kubernetes.labels.failure-domain_beta_kubernetes_io/region": "drop",
    "kubernetes.labels.failure-domain_beta_kubernetes_io/zone": "drop",
    "kubernetes.labels.component": numbered("label-component-"),
    "kubernetes.labels.controller-revision-hash": numbered("label-controller-revision-hash-"),
    "kubernetes.labels.controller-uid": uids(),
    "kubernetes.labels.github_account": numbered("github-account-"),
    "kubernetes.labels.helm_sh/chart": numbered("chart-"),
    "kubernetes.labels.heritage": k8s_labels_heritage,
    "kubernetes.labels.io_kompose_service": numbered("io_kopose_service-"),
    "kubernetes.labels.job-name": numbered("job-name-"),
    "kubernetes.labels.kubernetes_io/arch": k8s_labels_k8s_arch,
    "kubernetes.labels.kubernetes_io/hostname": numbered("kubernetes_io/hostname-"),
    "kubernetes.labels.kubernetes_io/os": k8s_labels_k8s_os,
    "kubernetes.labels.k8s-app": k8s_labels_k8s_app,
    "kubernetes.labels.logtype": passthrough,
    "kubernetes.labels.llama": "drop",
    "kubernetes.labels.name": k8s_labels_name,
    "kubernetes.labels.pod-template-generation": passthrough,
    "kubernetes.labels.pod-template-hash": numbered("label-pod-template-hash-"),
    "kubernetes.labels.release": numbered("release-"),
    "kubernetes.labels.statefulset_kubernetes_io/pod-name": numbered("statefulset_kubernetes_io/pod-name-"),
    "kubernetes.labels.tier": numbered("tier-"),
    "kubernetes.labels.watcher": "drop",
    "kubernetes.labels.version": "drop",
    "kubernetes.namespace": numbered("namespace"),
    "kubernetes.node.name": numbered("gke-apps-node-name-"),
    "kubernetes.node.cpu.allocatable.cores": passthrough,
    "kubernetes.node.cpu.capacity.cores": passthrough,
    "kubernetes.node.cpu.usage.core.ns": passthrough,
    "kubernetes.node.cpu.usage.nanocores": passthrough,
    "kubernetes.node.fs.available.bytes": passthrough,
    "kubernetes.node.fs.capacity.bytes": passthrough,
    "kubernetes.node.fs.inodes.count": passthrough,
    "kubernetes.node.fs.inodes.free": passthrough,
    "kubernetes.node.fs.inodes.used": passthrough,
    "kubernetes.node.fs.used.bytes": passthrough,
    "kubernetes.node.memory.allocatable.bytes": passthrough,
    "kubernetes.node.memory.available.bytes": passthrough,
    "kubernetes.node.memory.capacity.bytes": passthrough,
    "kubernetes.node.memory.majorpagefaults": passthrough,
    "kubernetes.node.memory.pagefaults": passthrough,
    "kubernetes.node.memory.rss.bytes": passthrough,
    "kubernetes.node.memory.usage.bytes": passthrough,
    "kubernetes.node.memory.workingset.bytes": passthrough,
    "kubernetes.node.network.rx.bytes": passthrough,
    "kubernetes.node.network.rx.errors": passthrough,
    "kubernetes.node.network.tx.bytes": passthrough,
    "kubernetes.node.network.tx.errors": passthrough,
    "kubernetes.node.pod.allocatable.total": passthrough,
    "kubernetes.node.pod.capacity.total": passthrough,
    "kubernetes.node.runtime.imagefs.available.bytes": passthrough,
    "kubernetes.node.runtime.imagefs.capacity.bytes": passthrough,
    "kubernetes.node.runtime.imagefs.used.bytes": passthrough,
    "kubernetes.node.start_time": passthrough,
    "kubernetes.node.status.ready": passthrough,
    "kubernetes.node.status.unschedulable": passthrough,
    "kubernetes.pod.cpu.usage.limit.pct": passthrough,
    "kubernetes.pod.cpu.usage.nanocores": passthrough,
    "kubernetes.pod.cpu.usage.node.pct": passthrough,
    "kubernetes.pod.host_ip": ips(),
    "kubernetes.pod.ip": ips(),
    "kubernetes.pod.memory.available.bytes": passthrough,
    "kubernetes.pod.memory.major_page_faults": passthrough,
    "kubernetes.pod.memory.page_faults": passthrough,
    "kubernetes.pod.memory.rss.bytes": passthrough,
    "kubernetes.pod.memory.usage.bytes": passthrough,
    "kubernetes.pod.memory.usage.limit.pct": passthrough,
    "kubernetes.pod.memory.usage.node.pct": passthrough,
    "kubernetes.pod.memory.working_set.bytes": passthrough,
    "kubernetes.pod.network.rx.bytes": passthrough,
    "kubernetes.pod.network.rx.errors": passthrough,
    "kubernetes.pod.network.tx.bytes": passthrough,
    "kubernetes.pod.network.tx.errors": passthrough,
    "kubernetes.pod.name": numbered("pod-name-pod-name-"),
    "kubernetes.pod.start_time": passthrough,
    "kubernetes.pod.status.phase": k8s_pod_status_phase,
    "kubernetes.pod.status.ready": passthrough,
    "kubernetes.pod.status.scheduled": passthrough,
    "kubernetes.pod.uid": uids(),
    "kubernetes.replicaset.name": numbered("replicaset-name-"),
    "kubernetes.statefulset.name": numbered("statefulset-name-"),
    "kubernetes.system.container": k8s_system_container,
    "kubernetes.system.cpu.usage.core.ns": passthrough,
    "kubernetes.system.cpu.usage.nanocores": passthrough,
    "kubernetes.system.memory.majorpagefaults": passthrough,
    "kubernetes.system.memory.pagefaults": passthrough,
    "kubernetes.system.memory.rss.bytes": passthrough,
    "kubernetes.system.memory.usage.bytes": passthrough,
    "kubernetes.system.memory.workingset.bytes": passthrough,
    "kubernetes.system.start_time": passthrough,
    "kubernetes.volume.fs.capacity.bytes": passthrough,
    "kubernetes.volume.fs.available.bytes": passthrough,
    "kubernetes.volume.fs.inodes.count": passthrough,
    "kubernetes.volume.fs.inodes.free": passthrough,
    "kubernetes.volume.fs.inodes.used": passthrough,
    "kubernetes.volume.fs.used.bytes": passthrough,
    "kubernetes.volume.name": numbered("volume-"),
    "metricset.name": passthrough,
    "metricset.period": passthrough,
    "service.address": numbered("service-address-"),
    "service.type": service_type,
}


def anon(path, it):
    result = {}
    for k, v in it.items():
        new_path = k if path == "" else path + "." + k
        if isinstance(v, dict):
            result[k] = anon(new_path, v)
            continue
        strategy = strategies.get(new_path)
        if not strategy:
            raise KeyError(f"Unknown key [{new_path}] with value [{v}]")
        if strategy == "drop":
            continue
        if isinstance(it, list):
            result[k] = [strategy(item) for item in v]
            continue
        result[k] = strategy(v)
    return result


count = 0
for line in sys.stdin:
    try:
        parsed = json.loads(line)
        anonymized = anon("", parsed)
        print(json.dumps(anonymized, separators=(",", ":")))
        count += 1
        if count % 1000 == 0:
            print(f"Processed {count:012d} documents", file=sys.stderr)
    except Exception as e:
        raise Exception(f"Error processing {line}") from e
