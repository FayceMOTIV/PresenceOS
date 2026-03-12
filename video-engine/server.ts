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
      entryPoint: path.resolve(process.cwd(), "src/index.ts"),
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

// ── Render endpoint V4 (1080x1920, new animations) ──────────────────
app.post("/render/breakout-v4", async (req, res) => {
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
    instagramHandle = "@monrestaurant",
    caption = "",
    accentColor = "#F59E0B",
  } = req.body;

  if (!originalPhotoUrl || !cutoutUrl) {
    return res.status(400).json({ error: "originalPhotoUrl and cutoutUrl required" });
  }

  const outputPath = path.join(os.tmpdir(), `breakout-v4-${Date.now()}.mp4`);

  try {
    const inputProps = {
      originalPhotoUrl,
      cutoutUrl,
      businessName,
      instagramHandle,
      caption,
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
      id: "BreakoutV4",
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
    console.error("[Remotion] V4 Render error:", err.message);
    res.status(500).json({ error: err.message });
  } finally {
    if (fs.existsSync(outputPath)) fs.unlinkSync(outputPath);
  }
});

// ── Render endpoint: PromoFlash ───────────────────────────────────────
app.post("/render/promo-flash", async (req, res) => {
  if (isWarming) {
    return res.status(503).json({ error: "Service warming up, retry in 30s" });
  }
  if (!bundleLocation || bundleError) {
    return res.status(500).json({ error: `Bundle unavailable: ${bundleError}` });
  }

  const {
    headline = "OFFRE SPECIALE",
    subheadline = "",
    promoCode = "",
    discount = "-20%",
    ctaText = "Reservez maintenant!",
    backgroundImage,
    primaryColor = "#E63946",
    brandName = "",
    validUntil = "",
  } = req.body;

  if (!backgroundImage) {
    return res.status(400).json({ error: "backgroundImage required" });
  }

  const outputPath = path.join(os.tmpdir(), `promo-flash-${Date.now()}.mp4`);

  try {
    const inputProps = {
      headline,
      subheadline,
      promoCode,
      discount,
      ctaText,
      backgroundImage,
      primaryColor,
      brandName,
      validUntil,
    };

    const chromiumOptions = {
      disableWebSecurity: true,
      ignoreCertificateErrors: true,
      enableMultiProcessOnLinux: true,
      gl: "swangle" as const,
    };

    const composition = await selectComposition({
      serveUrl: bundleLocation,
      id: "PromoFlash720",
      inputProps,
      chromiumOptions,
    });

    await renderMedia({
      composition,
      serveUrl: bundleLocation,
      codec: "h264",
      outputLocation: outputPath,
      inputProps,
      timeoutInMilliseconds: 180_000,
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
    console.error("[Remotion] PromoFlash render error:", err.message);
    res.status(500).json({ error: err.message });
  } finally {
    if (fs.existsSync(outputPath)) fs.unlinkSync(outputPath);
  }
});

// ── Render endpoint: RestaurantShowcase ──────────────────────────────
app.post("/render/restaurant-showcase", async (req, res) => {
  if (isWarming) {
    return res.status(503).json({ error: "Service warming up, retry in 30s" });
  }
  if (!bundleLocation || bundleError) {
    return res.status(500).json({ error: `Bundle unavailable: ${bundleError}` });
  }

  const {
    brandName = "Mon Restaurant",
    tagline = "Nos specialites",
    dishes = [],
    primaryColor = "#FF6B35",
    accentColor = "#FFFFFF",
    logoUrl = "",
  } = req.body;

  if (!dishes.length) {
    return res.status(400).json({ error: "At least one dish required" });
  }

  const outputPath = path.join(os.tmpdir(), `showcase-${Date.now()}.mp4`);

  try {
    const inputProps = {
      brandName,
      tagline,
      dishes,
      primaryColor,
      accentColor,
      logoUrl,
    };

    const chromiumOptions = {
      disableWebSecurity: true,
      ignoreCertificateErrors: true,
      enableMultiProcessOnLinux: true,
      gl: "swangle" as const,
    };

    const composition = await selectComposition({
      serveUrl: bundleLocation,
      id: "RestaurantShowcase720",
      inputProps,
      chromiumOptions,
    });

    await renderMedia({
      composition,
      serveUrl: bundleLocation,
      codec: "h264",
      outputLocation: outputPath,
      inputProps,
      timeoutInMilliseconds: 180_000,
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
    console.error("[Remotion] Showcase render error:", err.message);
    res.status(500).json({ error: err.message });
  } finally {
    if (fs.existsSync(outputPath)) fs.unlinkSync(outputPath);
  }
});

// ── Render endpoint: DailyStory ──────────────────────────────────────
app.post("/render/daily-story", async (req, res) => {
  if (isWarming) {
    return res.status(503).json({ error: "Service warming up, retry in 30s" });
  }
  if (!bundleLocation || bundleError) {
    return res.status(500).json({ error: `Bundle unavailable: ${bundleError}` });
  }

  const {
    slides = [],
    brandName = "Mon Restaurant",
    primaryColor = "#6C63FF",
    textPosition = "bottom",
  } = req.body;

  if (!slides.length) {
    return res.status(400).json({ error: "At least one slide required" });
  }

  const outputPath = path.join(os.tmpdir(), `story-${Date.now()}.mp4`);

  try {
    const inputProps = {
      slides,
      brandName,
      primaryColor,
      textPosition,
    };

    const chromiumOptions = {
      disableWebSecurity: true,
      ignoreCertificateErrors: true,
      enableMultiProcessOnLinux: true,
      gl: "swangle" as const,
    };

    const composition = await selectComposition({
      serveUrl: bundleLocation,
      id: "DailyStory720",
      inputProps,
      chromiumOptions,
    });

    await renderMedia({
      composition,
      serveUrl: bundleLocation,
      codec: "h264",
      outputLocation: outputPath,
      inputProps,
      timeoutInMilliseconds: 180_000,
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
    console.error("[Remotion] DailyStory render error:", err.message);
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
