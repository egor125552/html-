# Real model integration

The public Safari page uses BAS WebMAUS `runMAUSBasic` with `LANGUAGE=rus-RU` and `OUTFORMAT=TextGrid`. Audio is converted in-browser to mono PCM16 WAV at 16 kHz before upload. The returned TextGrid is parsed into word and phone intervals.
