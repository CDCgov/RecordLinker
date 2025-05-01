export enum PAGE_ERRORS {
  RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND",
  SERVER_ERROR = "SERVER_ERROR",
}

export class AppError extends Error {
  public readonly name: string;
  public readonly httpCode?: number;

  constructor(name: string, description: string, httpCode?: number) {
    super(description);

    Object.setPrototypeOf(this, new.target.prototype);
    this.name = name;
    this.httpCode = httpCode;

    Error.captureStackTrace(this);
  }
}
