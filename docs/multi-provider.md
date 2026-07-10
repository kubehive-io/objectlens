# Multi-Provider Connections

ObjectLens can connect to multiple object-storage systems at the same time. Each connection has a stable provider ID, a human-readable name, a provider type, endpoint information, region, credentials, and an optional default bucket.

A provider type is the implementation, such as `aws`, `ceph`, or `garage`. A provider connection is one configured target using that implementation. You can have many connections with the same type, such as AWS Production, AWS Backup, and AWS Sandbox.

This is useful when the same ObjectLens instance needs to browse separate environments:

- Ceph Homelab
- Garage Local
- AWS Production
- AWS Backup
- AWS Sandbox
- Ceph Lab

## Configuration

Create a `backend/data/providers/` directory, copy the example configurations, and edit them locally:

```bash
mkdir -p backend/data/providers
cp example/providers/*.yaml backend/data/providers/
```

Each provider is defined in its own file under the `backend/data/providers/` directory as a Kubernetes Custom Resource matching `kind: Provider` and `apiVersion: objectlens.kubehive.io/v1alpha1`.

Example (`backend/data/providers/ceph-homelab.yaml`):

```yaml
apiVersion: objectlens.kubehive.io/v1alpha1
kind: Provider
metadata:
  name: ceph-homelab
spec:
  id: ceph-homelab
  name: Ceph Homelab
  type: ceph
  description: Homelab Ceph RGW cluster
  endpoint_url: http://ceph-rgw.local:7480
  region: us-east-1
  access_key_id: ${CEPH_HOMELAB_ACCESS_KEY_ID}
  secret_access_key: ${CEPH_HOMELAB_SECRET_ACCESS_KEY}
  verify_ssl: false
  tags:
    - homelab
    - ceph
```

### Hot Reloading

If enabled in the configuration (`OBJECTLENS_PROVIDERS_RELOAD_INTERVAL=10`), the registry will automatically reload configuration changes from the `backend/data/providers/` directory at the specified interval in seconds, without requiring a service restart.

Provider IDs are used in URLs and API paths, so keep them stable and unique. Names are shown in the UI and can be changed later.

Environment placeholders use `${ENV_VAR}` syntax. If a referenced variable is missing, ObjectLens fails startup with a clear error.

## API Shape

Provider-scoped endpoints include the provider ID:

```text
GET /providers
GET /providers/{provider_id}/buckets
GET /providers/{provider_id}/buckets/{bucket}/objects
POST /providers/{provider_id}/objects/upload?bucket=&prefix=
```

`GET /providers` returns public connection details only. Secrets are never exposed.

## Metadata Scope

ObjectLens scopes indexed metadata by provider connection ID. This prevents collisions when two providers have the same bucket and object key names.

```mermaid
flowchart TD
  UI[Nuxt Frontend] --> API[FastAPI Backend]
  API --> Registry[Provider Registry]
  Registry --> Ceph[Ceph Homelab]
  Registry --> Garage[Garage Local]
  Registry --> AWS1[AWS Production]
  Registry --> AWS2[AWS Backup]
  API --> DB[(Metadata Index scoped by provider_id)]
```

## Security Notes

Do not commit `.objectlens.providers.yaml`. Keep real access keys in local secrets management, Kubernetes secrets, or another private configuration source. The checked-in `example/.objectlens.providers.example.yaml` intentionally uses placeholder credentials.
