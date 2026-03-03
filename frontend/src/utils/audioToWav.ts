const encodeWav = (samples: Float32Array, sampleRate: number): ArrayBuffer => {
  const bytesPerSample = 2;
  const blockAlign = bytesPerSample;
  const byteRate = sampleRate * blockAlign;
  const dataLength = samples.length * bytesPerSample;
  const buffer = new ArrayBuffer(44 + dataLength);
  const view = new DataView(buffer);

  const writeString = (offset: number, value: string) => {
    for (let index = 0; index < value.length; index += 1) {
      view.setUint8(offset + index, value.charCodeAt(index));
    }
  };

  writeString(0, "RIFF");
  view.setUint32(4, 36 + dataLength, true);
  writeString(8, "WAVE");
  writeString(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, byteRate, true);
  view.setUint16(32, blockAlign, true);
  view.setUint16(34, 16, true);
  writeString(36, "data");
  view.setUint32(40, dataLength, true);

  let offset = 44;
  for (let index = 0; index < samples.length; index += 1) {
    const sample = Math.max(-1, Math.min(1, samples[index]));
    const pcmValue = sample < 0 ? sample * 0x8000 : sample * 0x7fff;
    view.setInt16(offset, pcmValue, true);
    offset += bytesPerSample;
  }

  return buffer;
};

const toMono = (audioBuffer: AudioBuffer): Float32Array => {
  if (audioBuffer.numberOfChannels === 1) {
    return audioBuffer.getChannelData(0);
  }

  const channelCount = audioBuffer.numberOfChannels;
  const length = audioBuffer.length;
  const mono = new Float32Array(length);

  for (let channel = 0; channel < channelCount; channel += 1) {
    const data = audioBuffer.getChannelData(channel);
    for (let index = 0; index < length; index += 1) {
      mono[index] += data[index] / channelCount;
    }
  }

  return mono;
};

export const convertBlobToWavFile = async (
  blob: Blob,
  fileName = "recording.wav",
): Promise<File> => {
  const AudioContextCtor =
    window.AudioContext ||
    ((window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext as
      | typeof AudioContext
      | undefined);

  if (!AudioContextCtor) {
    throw new Error("AudioContext is not supported in this browser.");
  }

  const audioContext = new AudioContextCtor();

  try {
    const sourceBuffer = await blob.arrayBuffer();
    const decoded = await audioContext.decodeAudioData(sourceBuffer.slice(0));
    const mono = toMono(decoded);
    const wavBuffer = encodeWav(mono, decoded.sampleRate);

    return new File([wavBuffer], fileName, { type: "audio/wav" });
  } finally {
    await audioContext.close();
  }
};
