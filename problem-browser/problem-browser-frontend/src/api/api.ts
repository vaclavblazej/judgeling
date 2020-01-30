export type Method = 'GET' | 'POST' | 'PUT';

export interface ProblemDirectory {
  readonly content: string;
  readonly content_extension: string;
  readonly directories: string[];
  readonly parts?: any;
}

function call(address: string, method: Method, params?: any, data?: any) {
  if (data) data = JSON.stringify(data);
  const headers = {
    method: method,
    body: data,
    headers: new Headers({'Content-Type': 'application/json'})
  };
  const query = params ? '?' + Object.keys(params).map(k =>
    encodeURIComponent(k) + '=' + encodeURIComponent(params[k])
  ).join('&') : '';

  return fetch(address + query, headers)
}

// TODO: fetch from API
export async function getDirectory(directoryAddr: string[]): Promise<ProblemDirectory> {
  const address = "api/problem/" + directoryAddr.slice(1).join('/');
  return call(address, "GET").then((response) => response.json() as any)
}
