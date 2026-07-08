export type Bucket = {
  name: string;
  creation_date?: string | null;
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
  indexed_at: string;
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
    listObjects: (params: { bucket: string; prefix?: string; search?: string; limit?: number }) =>
      request<{ objects: ObjectMetadata[]; count: number }>("/objects", { query: params }),
    scanBucket: (bucket: string) =>
      request<ScanResponse>("/index/scan", {
        method: "POST",
        query: { bucket },
      }),
    presignDownload: (bucket: string, key: string) =>
      request<{ bucket: string; key: string; url: string }>("/objects/presign-download", {
        query: { bucket, key },
      }),
  };
}
