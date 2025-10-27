# rancher_client.py
import asyncio
from typing import Any, AsyncIterator, Dict, Iterable, Optional
import httpx
from urllib.parse import urljoin
from config import settings

class AsyncRancher:
    """
    Reusable async client for Rancher and its Kubernetes proxy.
    """
    def __init__(
        self,
        base_url: str,
        token: str,
        ca_bundle: Optional[str],
        timeout: float = 15.0,
        max_retries: int = 3,
    ) -> None:
        self.base_url = base_url
        self.token = token
        self.ca_bundle = ca_bundle
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: Optional[httpx.AsyncClient] = None

    async def start(self) -> None:
        if self._client is None:
            headers = {"Authorization": f"Bearer {self.token}"}
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=self.timeout,
                verify=self.ca_bundle if self.ca_bundle else True,
            )

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    # ---------- Internal retry wrapper ----------
    async def _request(
        self, method: str, url: str, **kwargs: Any
    ) -> httpx.Response:
        assert self._client, "Client not started"
        last_exc: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = await self._client.request(method, url, **kwargs)
                # Retry on 429 / 5xx
                if resp.status_code in (429, 500, 502, 503, 504):
                    raise httpx.HTTPStatusError("retryable status", request=resp.request, response=resp)
                return resp
            except (httpx.TransportError, httpx.HTTPStatusError) as e:
                last_exc = e
                # backoff: 0.25s, 0.5s, 1s...
                await asyncio.sleep(0.25 * (2 ** (attempt - 1)))
        assert last_exc
        raise last_exc

    # ---------- Rancher (v3) ----------
    async def rancher_get(self, path: str, **kwargs: Any) -> Dict[str, Any]:
        """
        path like '/v3/clusters' (leading slash ok). Returns JSON or raises.
        """
        url = urljoin(self.base_url + "/", path.lstrip("/"))
        resp = await self._request("GET", url, **kwargs)
        resp.raise_for_status()
        return resp.json()

    async def rancher_list_all(self, path: str, page_size: int = 100) -> Iterable[Dict[str, Any]]:
        """
        Iterate all items across Rancher pagination (v3 APIs).
        """
        url = urljoin(self.base_url + "/", path.lstrip("/"))
        params = {"limit": page_size}
        while True:
            resp = await self._request("GET", url, params=params)
            resp.raise_for_status()
            data = resp.json()
            # Common shape: {'data': [...], 'links': {'next': ...}}
            items = data.get("data") or []
            for item in items:
                yield item
            next_url = (data.get("links") or {}).get("next")
            if not next_url:
                break
            url = next_url
            params = {}  # next link already contains paging

    async def resolve_cluster_id(self, name_or_id: str) -> str:
        """
        Accepts either a Rancher cluster ID or a displayName; returns the cluster ID.
        """
        # If it looks like an ID, just return it
        if ":" in name_or_id or name_or_id.startswith("c-"):
            return name_or_id
        # Otherwise, search clusters by name
        async for c in self.rancher_list_all("/v3/clusters"):
            if c.get("name") == name_or_id or c.get("displayName") == name_or_id:
                cid = c.get("id")
                if cid:
                    return cid
        raise ValueError(f"Cluster not found: {name_or_id}")

    # ---------- Kubernetes via Rancher proxy ----------
    def _k8s_base(self, cluster_id: str) -> str:
        # K8s proxy root for a cluster:
        #   /k8s/clusters/{clusterId}/
        return f"/k8s/clusters/{cluster_id}/"

    async def k8s_get(self, cluster_id: str, k8s_path: str, **kwargs: Any) -> Dict[str, Any]:
        """
        k8s_path like 'api/v1/namespaces/kube-system/pods'
        """
        base = self._k8s_base(cluster_id)
        url = urljoin(self.base_url + "/", (base + k8s_path.lstrip("/")))
        resp = await self._request("GET", url, **kwargs)
        resp.raise_for_status()
        return resp.json()

    async def list_pods(self, cluster: str, namespace: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns a Kubernetes PodList. 'cluster' can be name or id.
        """
        cid = await self.resolve_cluster_id(cluster)
        path = "api/v1/pods" if not namespace else f"api/v1/namespaces/{namespace}/pods"
        return await self.k8s_get(cid, path)

# ---------- Singleton factory ----------
_rancher_singleton: Optional[AsyncRancher] = None

async def get_rancher() -> AsyncRancher:
    global _rancher_singleton
    if _rancher_singleton is None:
        _rancher_singleton = AsyncRancher(
            base_url=settings.RANCHER_URL,
            token=settings.RANCHER_TOKEN,
            ca_bundle=settings.RANCHER_CA_BUNDLE,
            timeout=settings.HTTP_TIMEOUT,
            max_retries=settings.MAX_RETRIES,
        )
        await _rancher_singleton.start()
    return _rancher_singleton

async def aclose_rancher() -> None:
    global _rancher_singleton
    if _rancher_singleton is not None:
        await _rancher_singleton.close()
        _rancher_singleton = None
