#!/usr/bin/env bash
# Mixe une voix off sur un épisode déjà monté : la musique baisse automatiquement
# quand la voix parle (sidechain), sortie normalisée à -14 LUFS (cible TikTok).
# Usage : engine/mix_voix.sh video_sans_voix.mp4 voix.(mp3|wav) musique.wav sortie.mp4 [decalage_s]
set -euo pipefail
VIDEO="$1"; VOIX="$2"; MUSIQUE="$3"; OUT="$4"; DECALAGE="${5:-0.15}"
MS=$(python3 -c "print(int(float('$DECALAGE')*1000))")
ffmpeg -y -loglevel error -i "$VIDEO" -i "$MUSIQUE" -i "$VOIX" -filter_complex "
  [2:a]aresample=48000,adelay=${MS}|${MS},highpass=f=80,acompressor=threshold=-18dB:ratio=3:attack=5:release=120,volume=1.0,apad,asplit=2[v1][vsc];
  [1:a]aresample=48000,volume=0.55[mus];
  [mus][vsc]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=350[musd];
  [musd][v1]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]" \
  -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart "$OUT"
echo "ok : $OUT"
