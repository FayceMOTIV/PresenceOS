import express from "express";
import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";
import * as path from "path";
import * as fs from "fs";
import * as os from "os";

const app = express();
app.use(express.json({ limit: "50mb" }));

const PORT = process.env.PORT || 3001;

// ── Bundle state ──────────────────────────────────────────────────────
let bundleLocation: string | null = null;
let bundleError: string | null = null;
let isWarming = true;

async function warmupBundle() {
  try {
    console.log("[Remotion] Starting bundle warmup...");
    bundleLocation = await bundle({
      entryPoint: path.resolve(__dirname, "./src/index.ts"),
      webpackOverride: (config) => config,
    });
    isWarming = false;
    console.log("[Remotion] Bundle ready:", bundleLocation);
  } catch (err: any) {
    bundleError = err.message;
    isWarming = false;
    console.error("[Remotion] Bundle warmup failed:", err.message);
  }
}

// ── Healthcheck — always 200 for Railway ──────────────────────────────
app.get("/health", (_req, res) => {
  res.json({
    status: isWarming ? "warming" : bundleError ? "error" : "ready",
    bundle: bundleLocation ? "loaded" : bundleError || "pending",
  });
});

// ── Render endpoint ───────────────────────────────────────────────────
app.post("/render/breakout", async (req, res) => {
  if (isWarming) {
    return res.status(503).json({ error: "Service warming up, retry in 30s" });
  }
  if (!bundleLocation || bundleError) {
    return res.status(500).json({ error: `Bundle unavailable: ${bundleError}` });
  }

  const {
    originalPhotoUrl,
    cutoutUrl,
    businessName = "Mon Restaurant",
    likesCount = 1200,
    instagramHandle = "@monrestaurant",
    accentColor = "#F59E0B",
  } = req.body;

  if (!originalPhotoUrl || !cutoutUrl) {
    return res.status(400).json({ error: "originalPhotoUrl and cutoutUrl required" });
  }

  const outputPath = path.join(os.tmpdir(), `breakout-${Date.now()}.mp4`);

  try {
    const inputProps = {
      originalPhotoUrl,
      cutoutUrl,
      businessName,
      likesCount,
      instagramHandle,
      accentColor,
    };

    const chromiumOptions = {
      disableWebSecurity: true,
      ignoreCertificateErrors: true,
      enableMultiProcessOnLinux: true,
      gl: "swangle" as const,
    };

    const composition = await selectComposition({
      serveUrl: bundleLocation,
      id: "BreakoutClip",
      inputProps,
      chromiumOptions,
    });

    await renderMedia({
      composition,
      serveUrl: bundleLocation,
      codec: "h264",
      outputLocation: outputPath,
      inputProps,
      timeoutInMilliseconds: 120_000,
      concurrency: 1,
      chromiumOptions,
      x264Preset: "superfast",
      offthreadVideoCacheSizeInBytes: 256 * 1024 * 1024,
    });

    const videoBuffer = fs.readFileSync(outputPath);
    const base64 = videoBuffer.toString("base64");

    res.json({
      success: true,
      video_base64: base64,
      size_bytes: videoBuffer.length,
    });
  } catch (err: any) {
    console.error("[Remotion] Render error:", err.message);
    res.status(500).json({ error: err.message });
  } finally {
    if (fs.existsSync(outputPath)) fs.unlinkSync(outputPath);
  }
});

// ── Start server + non-blocking warmup ────────────────────────────────
app.listen(PORT, () => {
  console.log(`[Remotion] Server listening on port ${PORT}`);
  warmupBundle();
});
