/**
 * Custom error types for AgentBreaker API client operations.
 */

export class ApiError extends Error {
  public readonly statusCode: number;
  public readonly data: any;

  constructor(message: string, statusCode: number, data?: any) {
    super(message);
    this.name = "ApiError";
    this.statusCode = statusCode;
    this.data = data;
    Object.setPrototypeOf(this, ApiError.prototype);
  }
}

export class NetworkError extends Error {
  constructor(message: string = "Failed to communicate with AgentBreaker backend.") {
    super(message);
    this.name = "NetworkError";
    Object.setPrototypeOf(this, NetworkError.prototype);
  }
}

