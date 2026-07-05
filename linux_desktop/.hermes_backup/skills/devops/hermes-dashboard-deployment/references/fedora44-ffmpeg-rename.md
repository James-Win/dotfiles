# Fedora 44 FFmpeg Package Rename

## Problem

Firefox on Fedora 44 logs decoder failures when playing any video:

```
WARNING: Decode error: NS_ERROR_DOM_MEDIA_FATAL_ERR (0x806e0005)
  mozilla::FFmpegDataDecoder<62>::InitDecoder(AVCodec*, AVDictionary**)
  Couldn't open avcodec
```

This produces the browser error: "no video with supported format and MIME
type found" — the error is generic and does not distinguish between a broken
codec and an upstream HTTP failure.

## Root Cause

Fedora 44 renamed the non-free FFmpeg packages. The old names
(`ffmpeg`, `ffmpeg-libs`) no longer resolve. Fedora 44 ships `ffmpeg-free`
instead, with libraries under `libav*-free` names.

## Fix

```bash
sudo dnf install -y ffmpeg-free gstreamer1-plugin-libav
```

Key packages pulled in:
- `ffmpeg-free.x86_64` — the CLI and shared libraries
- `libavcodec-free.x86_64` — the codec library Firefox loads via avcodec
- `gstreamer1-plugin-libav.x86_64` — GStreamer FFmpeg/LibAV plugin

## Confirmation

After install, verify in a new Firefox session — no new `Couldn't open
avcodec` lines should appear in the journal. Hard-refresh the dashboard
(Ctrl+Shift+R) to clear cached error state.
