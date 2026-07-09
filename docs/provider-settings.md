# Provider Settings

Provider settings expose safe runtime information for each provider connection. ObjectLens never returns access keys or secret keys through the API or UI.

## Safe Settings

`GET /providers/{provider_id}/settings` returns:

- provider ID
- config source
- whether secrets were loaded
- names of secret fields
- whether runtime editing is available

The PoC is read-only for configuration, so `editable` is `false`.

## Secret Loading

Provider YAML can reference secrets with environment placeholders:

```yaml
access_key_id: ${AWS_PROD_ACCESS_KEY_ID}
secret_access_key: ${AWS_PROD_SECRET_ACCESS_KEY}
```

If a referenced environment variable is missing, ObjectLens fails startup with a clear error naming the missing variable.

## Safe UI

The UI may show provider name, type, endpoint URL, region, tags, description, SSL verification mode, and whether secrets were loaded. It must not show the actual secret values.
