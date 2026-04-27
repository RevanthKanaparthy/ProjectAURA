const DEFAULT_BACKEND_URL = "https://projectaura-production.up.railway.app";

const jsonResponse = (body, status = 200) =>
  Response.json(body, {
    status,
    headers: {
      "Cache-Control": "no-store",
    },
  });

const getEnv = (name) => {
  const netlifyEnv = globalThis.Netlify?.env;
  return typeof netlifyEnv?.get === "function" ? netlifyEnv.get(name) : undefined;
};

const getBackendUrl = () => {
  const configuredUrl =
    getEnv("AURA_BACKEND_URL") ||
    getEnv("BACKEND_URL") ||
    getEnv("API_BASE_URL") ||
    DEFAULT_BACKEND_URL;

  return configuredUrl.replace(/\/+$/, "");
};

const getForwardPath = (requestUrl) => {
  const path = requestUrl.pathname.replace(/^\/api\/?/, "/");
  return `${path}${requestUrl.search}`;
};

const getForwardHeaders = (req) => {
  const headers = new Headers(req.headers);

  for (const header of [
    "accept-encoding",
    "connection",
    "content-length",
    "host",
    "x-nf-client-connection-ip",
  ]) {
    headers.delete(header);
  }

  return headers;
};

export default async (req) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { status: 204 });
  }

  const requestUrl = new URL(req.url);
  const upstreamUrl = `${getBackendUrl()}${getForwardPath(requestUrl)}`;

  try {
    const requestInit = {
      method: req.method,
      headers: getForwardHeaders(req),
      body: req.method === "GET" || req.method === "HEAD" ? undefined : req.body,
      redirect: "manual",
    };

    if (requestInit.body) {
      requestInit.duplex = "half";
    }

    const upstreamResponse = await fetch(upstreamUrl, requestInit);

    const responseHeaders = new Headers(upstreamResponse.headers);
    responseHeaders.set("Cache-Control", "no-store");
    responseHeaders.delete("content-encoding");
    responseHeaders.delete("content-length");
    responseHeaders.delete("transfer-encoding");

    const contentType = upstreamResponse.headers.get("content-type") || "";
    const bodyText = await upstreamResponse.text();

    if (
      upstreamResponse.status === 404 &&
      contentType.includes("application/json") &&
      bodyText.includes("Application not found")
    ) {
      return jsonResponse(
        {
          detail:
            "The configured backend service is unavailable. Set AURA_BACKEND_URL to a running FastAPI backend for this Netlify site.",
        },
        502,
      );
    }

    return new Response(bodyText, {
      status: upstreamResponse.status,
      statusText: upstreamResponse.statusText,
      headers: responseHeaders,
    });
  } catch (error) {
    console.error("API proxy request failed", error);

    return jsonResponse(
      {
        detail:
          "The backend service could not be reached. Check that AURA_BACKEND_URL points to a running FastAPI backend.",
      },
      502,
    );
  }
};

export const config = {
  path: "/api/*",
};
