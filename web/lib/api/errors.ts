export class MdbApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code?: string,
  ) {
    super(message);
    this.name = "MdbApiError";
  }
}

export function isNotFound(error: unknown) {
  return error instanceof MdbApiError && error.status === 404;
}
