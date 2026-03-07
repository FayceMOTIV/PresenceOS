import express from "express";
import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";
import path from "path";
import fs from "fs";
import os from "os";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
app.use(express.json({ limit: "10mb" }));

let cachedBundleLocation: string | null = null;

app.get("/health", (_req, res) => res.json({ status: "ok" }));

app.post("/render/breakout", async (req, res) => {
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
    // Bundle once, reuse for subsequent renders
    if (!cachedBundleLocation) {
      console.log("[Remotion] Bundling composition (first time)...");
      cachedBundleLocation = await bundle({
        entryPoint: path.resolve(__dirname, "./src/index.ts"),
        webpackOverride: (config) => config,
      });
      console.log("[Remotion] Bundle cached.");
    }

    const inputProps = {
      originalPhotoUrl,
      cutoutUrl,
      businessName,
      likesCount,
      instagramHandle,
      accentColor,
    };

    const composition = await selectComposition({
      serveUrl: cachedBundleLocation,
      id: "BreakoutClip",
      inputProps,
    });

    await renderMedia({
      composition,
      serveUrl: cachedBundleLocation,
      codec: "h264",
      outputLocation: outputPath,
      inputProps,
    });

    const videoBuffer = fs.readFileSync(outputPath);
    res.set("Content-Type", "video/mp4");
    res.set("Content-Disposition", 'attachment; filename="breakout.mp4"');
    res.send(videoBuffer);
  } catch (err: any) {
    console.error("[Remotion] Render error:", err.message);
    res.status(500).json({ error: err.message });
  } finally {
    if (fs.existsSync(outputPath)) fs.unlinkSync(outputPath);
  }
});

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => console.log(`[Remotion] Server running on port ${PORT}`));
