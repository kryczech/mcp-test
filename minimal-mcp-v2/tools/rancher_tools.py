# tools/rancher_tools.py
from typing import Optional
from app import mcp
from rancher_client import get_rancher

@mcp.tool()
async def rancher_clusters() -> list[dict]:
    """List Rancher clusters (basic fields)."""
    client = await get_rancher()
    clusters = []
    async for c in client.rancher_list_all("/v3/clusters"):
        clusters.append({
            "id": c.get("id"),
            "name": c.get("name"),
            "displayName": c.get("displayName"),
            "state": c.get("state"),
            "version": (c.get("rancherKubernetesEngineConfig") or {}).get("kubernetesVersion"),
        })
    return clusters

@mcp.tool()
async def k8s_pods(cluster: str, namespace: Optional[str] = None) -> list[dict]:
    """
    Get simplified list of pods via Rancher k8s proxy.
    Args:
        cluster: Rancher cluster ID (e.g., 'c-abcde') or display name
        namespace: Optional namespace to filter pods. If None, lists pods from all namespaces.
    Returns:
        List of pods with basic information similar to kubectl get pods output.
    """
    client = await get_rancher()
    response = await client.list_pods(cluster, namespace)
    
    pods = []
    for pod in response.get("items", []):
        # Extract basic pod information
        pod_info = {
            "name": pod.get("metadata", {}).get("name"),
            "namespace": pod.get("metadata", {}).get("namespace"),
            "ready": f"{sum(1 for c in pod.get('status', {}).get('containerStatuses', []) if c.get('ready'))}/{len(pod.get('status', {}).get('containerStatuses', []))}",
            "status": pod.get("status", {}).get("phase"),
            "age": pod.get("metadata", {}).get("creationTimestamp"),
        }
        pods.append(pod_info)
    
    return pods
