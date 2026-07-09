# Garage Provider

Garage is an S3-compatible object storage server designed for small, self-hosted, and distributed environments. ObjectLens supports Garage because it makes the project easier to run without AWS or Ceph, especially for local development, air-gapped labs, and small homelab deployments.

## Why Garage

Garage gives ObjectLens a lightweight local provider target while keeping the same S3-compatible provider abstraction used by Ceph RGW. This lets developers test bucket browsing, uploads, previews, deletes, rename, move, and merge flows without cloud credentials.

## Environment Variables

```env
OBJECTLENS_PROVIDER=garage

GARAGE_S3_ENDPOINT_URL=http://localhost:3900
GARAGE_S3_REGION=garage
GARAGE_S3_ACCESS_KEY_ID=garage
GARAGE_S3_SECRET_ACCESS_KEY=garage
GARAGE_S3_DEFAULT_BUCKET=
GARAGE_S3_VERIFY_SSL=false
```

`GARAGE_S3_ACCESS_KEY_ID` and `GARAGE_S3_SECRET_ACCESS_KEY` must match a Garage key with access to the buckets you want ObjectLens to show. `GET /buckets` reflects the bucket visibility granted to those credentials.

## Running ObjectLens Against Garage

Start or connect to a Garage instance with the S3 API listening on `localhost:3900`, then configure ObjectLens:

```bash
cp .env.example .env
```

Edit `.env`:

```env
OBJECTLENS_PROVIDER=garage
GARAGE_S3_ENDPOINT_URL=http://localhost:3900
```

Then run:

```bash
devbox shell
just install
just dev
```

Open:

```text
Frontend: http://localhost:3000
Backend provider: http://localhost:8000/provider
```

The provider endpoint should report:

```json
{
  "provider": "garage",
  "display_name": "Garage"
}
```

Secrets are never returned from the provider endpoint.

## Optional Docker Compose Service

ObjectLens includes an optional Garage compose profile:

```bash
docker compose --profile garage up garage
```

The compose service exposes:

```text
S3 API: http://localhost:3900
```

Garage still needs normal first-time cluster, key, and bucket setup before ObjectLens can list or upload objects. After creating a Garage key and granting it bucket access, put that key in `.env`:

```env
OBJECTLENS_PROVIDER=garage
GARAGE_S3_ENDPOINT_URL=http://localhost:3900
GARAGE_S3_ACCESS_KEY_ID=<garage-access-key-id>
GARAGE_S3_SECRET_ACCESS_KEY=<garage-secret-access-key>
```
