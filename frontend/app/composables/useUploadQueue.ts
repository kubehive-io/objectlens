const queuedFiles = shallowRef<File[]>([]);

export function useUploadQueue() {
  const files = queuedFiles;

  function setFiles(nextFiles: FileList | File[]) {
    files.value = Array.from(nextFiles);
  }

  function addFiles(nextFiles: FileList | File[]) {
    files.value = [...files.value, ...Array.from(nextFiles)];
  }

  function removeFile(index: number) {
    files.value = files.value.filter((_, itemIndex) => itemIndex !== index);
  }

  function clearFiles() {
    files.value = [];
  }

  return {
    files,
    addFiles,
    setFiles,
    removeFile,
    clearFiles,
  };
}
