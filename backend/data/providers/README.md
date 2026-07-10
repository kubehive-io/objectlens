# Provider Configurations

Place your S3/Ceph/Garage provider configuration files in this directory. 

Each file must configure exactly **one** provider, matching the `Provider` schema.

## Format Example

Create a file (e.g., `backend/data/providers/my-ceph.yaml`):

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

## Getting Started

To populate this directory with development examples:

```bash
cp example/providers/*.yaml backend/data/providers/
```

Reference environment variables in your YAML files with `${ENV_VAR}` syntax. Ensure those variables are defined in your shell or local `.env` file.
