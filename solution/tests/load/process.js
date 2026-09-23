import http from "k6/http";
import { check, sleep } from "k6";
import exec from "k6/execution";
import { Rate, Trend } from "k6/metrics";

const profile = (__ENV.PROFILE || "smoke").toLowerCase();
const baseUrl = (__ENV.BASE_URL || "http://127.0.0.1:8080").replace(/\/$/, "");
const runId = __ENV.RUN_ID || `${Date.now()}`;

function positiveNumber(name, fallback) {
  const value = Number(__ENV[name] || fallback);
  if (!Number.isFinite(value) || value <= 0) {
    throw new Error(`${name} must be a positive number, got: ${__ENV[name]}`);
  }
  return value;
}

function positiveInteger(name, fallback) {
  const value = positiveNumber(name, fallback);
  if (!Number.isInteger(value)) {
    throw new Error(`${name} must be an integer, got: ${value}`);
  }
  return value;
}

const maskRequestDuration = new Trend("mask_request_duration", true);
const unmaskRequestDuration = new Trend("unmask_request_duration", true);
const cycleDuration = new Trend("business_cycle_duration", true);
const benchmarkErrors = new Rate("benchmark_errors");

function smokeOptions() {
  return {
    scenarios: {
      smoke: {
        executor: "constant-vus",
        vus: positiveInteger("VUS", 1),
        duration: __ENV.DURATION || "10s",
        gracefulStop: "5s",
      },
    },
    thresholds: {
      http_req_failed: ["rate<0.01"],
      http_req_duration: ["p(95)<1000"],
      benchmark_errors: ["rate<0.01"],
      checks: ["rate>0.99"],
    },
  };
}

function loadOptions() {
  const targetHttpRps = positiveInteger("TARGET_HTTP_RPS", 1000);
  const warmupHttpRps = positiveInteger("WARMUP_HTTP_RPS", 100);

  if (targetHttpRps % 2 !== 0 || warmupHttpRps % 2 !== 0) {
    throw new Error(
      "TARGET_HTTP_RPS and WARMUP_HTTP_RPS must be even: one iteration sends exactly two HTTP requests",
    );
  }

  const warmupDuration = __ENV.WARMUP_DURATION || "20s";

  return {
    scenarios: {
      warmup: {
        executor: "constant-arrival-rate",
        rate: warmupHttpRps / 2,
        timeUnit: "1s",
        duration: warmupDuration,
        preAllocatedVUs: positiveInteger("WARMUP_PREALLOCATED_VUS", 100),
        maxVUs: positiveInteger("WARMUP_MAX_VUS", 500),
        // Do not let slow warm-up iterations overlap with the measured phase.
        gracefulStop: "0s",
      },
      benchmark: {
        executor: "constant-arrival-rate",
        rate: targetHttpRps / 2,
        timeUnit: "1s",
        duration: __ENV.DURATION || "60s",
        startTime: warmupDuration,
        preAllocatedVUs: positiveInteger("PREALLOCATED_VUS", 1000),
        maxVUs: positiveInteger("MAX_VUS", 2000),
        gracefulStop: "30s",
      },
    },
    thresholds: {
      "http_req_failed{scenario:benchmark}": ["rate<0.01"],
      "http_req_duration{scenario:benchmark}": ["p(95)<1000"],
      "benchmark_errors{scenario:benchmark}": ["rate<0.01"],
      "checks{scenario:benchmark}": ["rate>0.99"],
      "dropped_iterations{scenario:benchmark}": ["count==0"],
    },
  };
}

if (profile !== "smoke" && profile !== "load") {
  throw new Error(`PROFILE must be smoke or load, got: ${profile}`);
}

export const options = {
  ...(profile === "load" ? loadOptions() : smokeOptions()),
  summaryTrendStats: ["avg", "min", "med", "p(90)", "p(95)", "p(99)", "max"],
};

const headers = { "Content-Type": "application/json" };
const source =
  "Клиент Иван Петров, телефон +7 999 123-45-67, email ivan@example.com, ИНН 7707083893";

function responseResult(response) {
  try {
    const result = response.json("result");
    return typeof result === "string" ? result : null;
  } catch (_) {
    return null;
  }
}

export default function () {
  const iteration = exec.scenario.iterationInTest;
  const payloadId = `${runId}-${exec.scenario.name}-${exec.vu.idInTest}-${iteration}`;
  const cycleStartedAt = Date.now();

  const masked = http.post(
    `${baseUrl}/process`,
    JSON.stringify({ payload: source, payload_id: payloadId }),
    { headers, tags: { operation: "mask" } },
  );
  if (exec.scenario.name !== "warmup") {
    maskRequestDuration.add(masked.timings.duration);
  }
  const maskedResult = responseResult(masked);
  const maskOk =
    masked.status === 200 &&
    maskedResult !== null &&
    !maskedResult.includes("ivan@example.com") &&
    !maskedResult.includes("+7 999 123-45-67");
  check(masked, {
    "mask returns HTTP 200": () => masked.status === 200,
    "mask hides known PII": () => maskOk,
  });
  benchmarkErrors.add(!maskOk, { operation: "mask" });

  // Always issue the second request so every iteration represents exactly two
  // HTTP requests, even when the mask response is malformed or unsuccessful.
  const restored = http.post(
    `${baseUrl}/process`,
    JSON.stringify({ payload: maskedResult || "", payload_id: payloadId }),
    { headers, tags: { operation: "unmask" } },
  );
  if (exec.scenario.name !== "warmup") {
    unmaskRequestDuration.add(restored.timings.duration);
  }
  const restoredResult = responseResult(restored);
  const restoreOk = restored.status === 200 && restoredResult === source;
  check(restored, {
    "unmask returns HTTP 200": () => restored.status === 200,
    "unmask restores source exactly": () => restoreOk,
  });
  benchmarkErrors.add(!restoreOk, { operation: "unmask" });

  if (exec.scenario.name !== "warmup") {
    cycleDuration.add(Date.now() - cycleStartedAt);
  }

  if (profile === "smoke") {
    sleep(positiveNumber("SMOKE_SLEEP_SECONDS", 0.1));
  }
}
