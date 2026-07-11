export type Bucket = {
  name: string;
  creation_date?: string | null;
};

export type BucketDetails = {
  provider: string;
  provider_id?: string | null;
  provider_name?: string | null;
  name: string;
  bucket?: string | null;
  creation_date?: string | null;
  indexed_object_count: number;
  indexed_total_size: number;
  last_indexed_at?: string | null;
  largest_objects?: ObjectMetadata[];
  recent_objects?: ObjectMetadata[];
  top_prefixes?: PrefixSummary[];
};

export type HealthResponse = {
  status: string;
  service: string;
};

export type ProviderInfo = {
  id?: string | null;
  name?: string | null;
  type?: string | null;
  provider: string;
  display_name: string;
  endpoint_url?: string | null;
  region?: string | null;
  default_bucket?: string | null;
};

export type ProviderConnection = {
  id: string;
  name: string;
  type: string;
  display_name: string;
  description?: string | null;
  endpoint_url?: string | null;
  region: string;
  default_bucket?: string | null;
  verify_ssl: boolean;
  tags: string[];
  error?: string | null;
};

export type ProviderStatus = {
  provider_id: string;
  status: string;
  can_list_buckets: boolean;
  visible_bucket_count: number;
  message: string;
};

export type ProviderSettings = {
  provider_id: string;
  config_source: string;
  secrets_loaded: boolean;
  secret_fields: string[];
  editable: boolean;
};

export type ObjectMetadata = {
  provider: string;
  bucket: string;
  key: string;
  size: number;
  etag?: string | null;
  last_modified?: string | null;
  storage_class?: string | null;
  content_type?: string | null;
  metadata?: Record<string, unknown>;
  indexed_at?: string | null;
};

export type PrefixSummary = {
  prefix: string;
  object_count: number;
  total_size: number;
};

export type ActivityLog = {
  id: string;
  type: "success" | "warning" | "info" | "error";
  title: string;
  description: string;
  timestamp: string;
  duration?: string | null;
};

export type BucketSummary = {
  provider: string;
  bucket: string;
  indexed_object_count: number;
  indexed_total_size: number;
  last_indexed_at?: string | null;
  largest_objects: ObjectMetadata[];
  recent_objects: ObjectMetadata[];
  top_prefixes: PrefixSummary[];
};

export type BucketSettings = {
  bucket: string;
  provider_id: string;
  versioning: string;
  lifecycle: string;
  policy: string;
};

export type BucketPrefix = {
  name: string;
  prefix: string;
  object_count: number;
};

export type BucketBrowserItem = {
  type: "prefix" | "object";
  name: string;
  icon: "folder" | "json" | "csv" | "parquet" | "image" | "file";
  prefix?: string | null;
  key?: string | null;
  size?: number | null;
  content_type?: string | null;
  storage_class?: string | null;
  last_modified?: string | null;
};

export type Pagination = {
  limit: number;
  offset: number;
  next_offset?: number | null;
  previous_offset?: number | null;
  has_next: boolean;
  has_previous: boolean;
};

export type BucketObjectListing = {
  bucket: string;
  prefix: string;
  delimiter?: string | null;
  mode: "browse" | "search";
  limit: number;
  offset: number;
  total_objects: number;
  items: BucketBrowserItem[];
  pagination: Pagination;
};

export type ObjectPreview = {
  bucket: string;
  key: string;
  preview_type: "json" | "csv" | "parquet" | "image" | "unsupported";
  content_type?: string | null;
  size?: number | null;
  truncated: boolean;
  text?: string | null;
  headers?: string[] | null;
  rows?: Record<string, unknown>[] | null;
  schema_fields?: { name: string; type: string }[] | null;
  image_url?: string | null;
  download_url?: string | null;
  reason?: string | null;
};

export type ScanResponse = {
  bucket: string;
  scanned: number;
  indexed: number;
};

export type DeletePrefixResponse = {
  bucket: string;
  prefix: string;
  deleted_count: number;
  errors: string[];
};

export type OperationSummary = {
  operation_id: string;
  status: string;
  total_objects: number;
  moved_objects: number;
  skipped_objects?: number;
  conflicts: string[];
  errors: string[];
  source_prefix?: string;
  target_prefix?: string;
};

export type OperationStatus = {
  operation_id: string;
  type: string;
  status: string;
  total: number;
  completed: number;
  failed: number;
  message: string;
  errors: string[];
};

export function useObjectLensApi() {
  const config = useRuntimeConfig();
  const baseUrl = config.public.apiBaseUrl;

  async function request<T>(
    path: string,
    options?: {
      method?: "GET" | "POST" | "DELETE";
      query?: Record<string, string | number | undefined>;
      body?: BodyInit | Record<string, unknown>;
    },
  ): Promise<T> {
    try {
      return await $fetch<T>(path, {
        baseURL: baseUrl,
        ...options,
      });
    } catch (error) {
      const fetchError = error as { data?: { detail?: string }; message?: string };
      throw new Error(fetchError.data?.detail || fetchError.message || "ObjectLens API request failed");
    }
  }

  return {
    health: () => request<HealthResponse>("/health"),
    provider: () => request<ProviderInfo>("/provider"),
    listProviders: () => request<ProviderConnection[]>("/providers"),
    reloadProviders: () =>
      request<ProviderConnection[]>("/providers/reload", { method: "POST" }),
    providerConnection: (providerId: string) =>
      request<ProviderConnection>(`/providers/${encodeURIComponent(providerId)}`),
    providerStatus: (providerId: string) =>
      request<ProviderStatus>(`/providers/${encodeURIComponent(providerId)}/status`),
    providerSettings: (providerId: string) =>
      request<ProviderSettings>(`/providers/${encodeURIComponent(providerId)}/settings`),
    listBuckets: () => request<{ buckets: Bucket[] }>("/buckets"),
    listProviderBuckets: (providerId: string) =>
      request<{ buckets: Bucket[] }>(`/providers/${encodeURIComponent(providerId)}/buckets`),
    bucketDetails: (bucket: string) => request<BucketDetails>(`/buckets/${encodeURIComponent(bucket)}`),
    providerBucketDetails: (providerId: string, bucket: string) =>
      request<BucketDetails>(
        `/providers/${encodeURIComponent(providerId)}/buckets/${encodeURIComponent(bucket)}`,
      ),
    bucketSummary: (bucket: string) => request<BucketSummary>(`/buckets/${encodeURIComponent(bucket)}/summary`),
    providerBucketSummary: (providerId: string, bucket: string) =>
      request<BucketSummary>(
        `/providers/${encodeURIComponent(providerId)}/buckets/${encodeURIComponent(bucket)}/summary`,
      ),
    providerBucketSettings: (providerId: string, bucket: string) =>
      request<BucketSettings>(
        `/providers/${encodeURIComponent(providerId)}/buckets/${encodeURIComponent(bucket)}/settings`,
      ),
    listObjects: (params: { bucket: string; prefix?: string; search?: string; limit?: number; offset?: number }) =>
      request<{ objects: ObjectMetadata[]; count: number }>("/objects", { query: params }),
    listBucketObjects: (
      bucket: string,
      params: {
        prefix?: string;
        search?: string;
        limit?: number;
        offset?: number;
        delimiter?: string;
        providerId?: string;
      },
    ) =>
      request<BucketObjectListing>(
        params.providerId
          ? `/providers/${encodeURIComponent(params.providerId)}/buckets/${encodeURIComponent(bucket)}/objects`
          : `/buckets/${encodeURIComponent(bucket)}/objects`,
        {
        query: params,
        },
      ),
    scanBucket: (bucket: string, providerId?: string) =>
      request<ScanResponse>(providerId ? `/providers/${encodeURIComponent(providerId)}/index/scan` : "/index/scan", {
        method: "POST",
        query: { bucket },
      }),
    presignDownload: (bucket: string, key: string, providerId?: string) =>
      request<{ bucket: string; key: string; url: string }>(
        providerId
          ? `/providers/${encodeURIComponent(providerId)}/objects/presign-download`
          : "/objects/presign-download",
        {
        query: { bucket, key },
        },
      ),
    objectPreview: (bucket: string, key: string, providerId?: string) =>
      request<ObjectPreview>(providerId ? `/providers/${encodeURIComponent(providerId)}/objects/preview` : "/objects/preview", {
        query: { bucket, key },
      }),
    objectMetadata: (bucket: string, key: string, providerId?: string) =>
      request<ObjectMetadata>(providerId ? `/providers/${encodeURIComponent(providerId)}/objects/metadata` : "/objects/metadata", {
        query: { bucket, key },
      }),
    deleteObject: (bucket: string, key: string, providerId?: string) =>
      request<{ bucket: string; key: string; deleted: boolean }>(
        providerId ? `/providers/${encodeURIComponent(providerId)}/objects` : "/objects",
        {
        method: "DELETE",
        query: { bucket, key },
        },
      ),
    deletePrefix: (bucket: string, prefix: string, providerId?: string) =>
      request<DeletePrefixResponse>(providerId ? `/providers/${encodeURIComponent(providerId)}/prefixes` : "/prefixes", {
        method: "DELETE",
        query: { bucket, prefix },
      }),
    uploadObject: (
      bucket: string,
      prefix: string,
      file: File,
      providerId?: string,
      key?: string,
      cacheControl?: string,
      metadata?: Record<string, string>,
    ) => {
      const body = new FormData();
      body.append("file", file);
      return request<ObjectMetadata>(providerId ? `/providers/${encodeURIComponent(providerId)}/objects/upload` : "/objects/upload", {
        method: "POST",
        query: {
          bucket,
          prefix,
          ...(key ? { key } : {}),
          ...(cacheControl ? { cache_control: cacheControl } : {}),
          ...(metadata ? { metadata: JSON.stringify(metadata) } : {}),
        },
        body,
      });
    },
    renameObject: (
      payload: { bucket: string; source_key: string; target_key: string; overwrite: boolean },
      providerId?: string,
    ) =>
      request<ObjectMetadata>(providerId ? `/providers/${encodeURIComponent(providerId)}/objects/rename` : "/objects/rename", {
        method: "POST",
        body: payload,
      }),
    renamePrefix: (
      payload: { bucket: string; source_prefix: string; target_prefix: string; overwrite: boolean },
      providerId?: string,
    ) =>
      request<OperationSummary>(providerId ? `/providers/${encodeURIComponent(providerId)}/prefixes/rename` : "/prefixes/rename", {
        method: "POST",
        body: payload,
      }),
    moveObjects: (payload: {
      bucket: string;
      items: Array<{ type: "object" | "prefix"; key?: string; prefix?: string }>;
      target_prefix: string;
      overwrite: boolean;
    }, providerId?: string) =>
      request<OperationSummary>(providerId ? `/providers/${encodeURIComponent(providerId)}/objects/move` : "/objects/move", {
        method: "POST",
        body: payload,
      }),
    mergePrefixes: (payload: {
      bucket: string;
      source_prefix: string;
      target_prefix: string;
      conflict_strategy: "fail" | "skip" | "overwrite";
    }, providerId?: string) =>
      request<OperationSummary>(providerId ? `/providers/${encodeURIComponent(providerId)}/prefixes/merge` : "/prefixes/merge", {
        method: "POST",
        body: payload,
      }),
    operationStatus: (operationId: string) => request<OperationStatus>(`/operations/${operationId}`),
    listActivities: (limit?: number) =>
      request<ActivityLog[]>("/activity", {
        query: { limit },
      }),
  };
}
