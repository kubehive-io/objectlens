# Ceph Provider

Ceph RGW is the first supported ObjectLens provider.

The provider uses the S3-compatible API through boto3. This keeps the implementation practical because Ceph Object Gateway already exposes common S3 operations such as bucket listing, object listing, metadata reads, and presigned downloads.

Bucket visibility comes from Ceph RGW credentials. `GET /buckets` calls the provider API and returns only buckets the configured access key can list. If Ceph RGW denies bucket listing, ObjectLens returns a clear API error instead of falling back to static bucket names.

## Environment Variables

```env
OBJECTLENS_PROVIDER=ceph

CEPH_S3_ENDPOINT_URL=http://localhost:9000
CEPH_S3_REGION=us-east-1
CEPH_S3_ACCESS_KEY_ID=minioadmin
CEPH_S3_SECRET_ACCESS_KEY=minioadmin
CEPH_S3_DEFAULT_BUCKET=
CEPH_S3_VERIFY_SSL=false
```

## Homelab Ceph RGW

For a homelab Ceph cluster, point `CEPH_S3_ENDPOINT_URL` at the RGW endpoint:

```env
CEPH_S3_ENDPOINT_URL=https://rgw.example.internal
CEPH_S3_REGION=us-east-1
CEPH_S3_ACCESS_KEY_ID=<access-key>
CEPH_S3_SECRET_ACCESS_KEY=<secret-key>
CEPH_S3_DEFAULT_BUCKET=<optional-default-bucket>
CEPH_S3_VERIFY_SSL=true
```

If the endpoint uses a private certificate authority, configure the host trust store or set up a verified certificate chain rather than disabling SSL verification for shared environments.

## Security Notes

- Do not commit real Ceph credentials.
- Use Kubernetes Secrets for deployment.
- Prefer scoped credentials with the minimum bucket access needed.
- Rotate credentials if they are exposed in shell history, logs, or local files.

## Preview Limitations

- JSON and CSV previews read only a bounded byte range.
- Image previews return a presigned URL instead of proxying large bytes through the API.
- Parquet preview is optional and requires `pyarrow`; without it, ObjectLens returns an unsupported preview response with a download URL.
- Preview and download activity should be audited in a later phase.
