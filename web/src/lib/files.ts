export const ACCEPTED_GUIDELINE_EXTENSIONS = ['.txt', '.md', '.markdown', '.pdf', '.docx'];
export const MAX_GUIDELINE_MB = 10;

export const fileExtension = (name: string) => /\.[a-z0-9]+$/i.exec(name)?.[0]?.toLowerCase() ?? '';

/** Reads a File into bytes; falls back to FileReader where Blob.arrayBuffer is unavailable (jsdom). */
export async function fileToBytes(file: File): Promise<Uint8Array<ArrayBuffer>> {
  if (typeof file.arrayBuffer === 'function') return new Uint8Array(await file.arrayBuffer());
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      if (reader.result instanceof ArrayBuffer) resolve(new Uint8Array(reader.result));
      else reject(new Error('Unexpected FileReader result'));
    };
    reader.onerror = () => reject(reader.error ?? new Error('read failed'));
    reader.readAsArrayBuffer(file);
  });
}
