export type Bucket = {
  name: string;
  creation_date?: string | null;
};

export type BucketDetails = {
  provider: string;
  name: string;
  creation_date?: string | null;
  indexed_object_count: number;
  indexed_total_size: number;
  last_indexed_at?: string | null;
};

export type HealthResponse = {
  status: string;
  service: string;
};

export type ProviderInfo = {
  provider: string;
  display_name: string;
  endpoint_url?: string | null;
  default_bucket?: string | null;
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

export function useObjectLensApi() {
  const config = useRuntimeConfig();
  const baseUrl = config.public.apiBaseUrl;

  async function request<T>(
    path: string,
    options?: { method?: "GET" | "POST"; query?: Record<string, string | number | undefined> },
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
    listBuckets: () => request<{ buckets: Bucket[] }>("/buckets"),
    bucketDetails: (bucket: string) => request<BucketDetails>(`/buckets/${encodeURIComponent(bucket)}`),
    bucketSummary: (bucket: string) => request<BucketSummary>(`/buckets/${encodeURIComponent(bucket)}/summary`),
    listObjects: (params: { bucket: string; prefix?: string; search?: string; limit?: number; offset?: number }) =>
      request<{ objects: ObjectMetadata[]; count: number }>("/objects", { query: params }),
    listBucketObjects: (
      bucket: string,
      params: { prefix?: string; search?: string; limit?: number; offset?: number; delimiter?: string },
    ) =>
      request<BucketObjectListing>(`/buckets/${encodeURIComponent(bucket)}/objects`, {
        query: params,
      }),
    scanBucket: (bucket: string) =>
      request<ScanResponse>("/index/scan", {
        method: "POST",
        query: { bucket },
      }),
    presignDownload: (bucket: string, key: string) =>
      request<{ bucket: string; key: string; url: string }>("/objects/presign-download", {
        query: { bucket, key },
      }),
    objectPreview: (bucket: string, key: string) =>
      request<ObjectPreview>("/objects/preview", {
        query: { bucket, key },
      }),
    objectMetadata: (bucket: string, key: string) =>
      request<ObjectMetadata>("/objects/metadata", {
        query: { bucket, key },
      }),
  };
}
