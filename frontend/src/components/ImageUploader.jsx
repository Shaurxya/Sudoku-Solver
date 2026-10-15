import React, { useRef, useState, useEffect } from 'react';
import {
  Upload,
  Image as ImageIcon,
  CheckCircle,
  AlertCircle,
  Camera,
  Layers,
  Sparkles
} from 'lucide-react';

export default function ImageUploader({
  onImageSelected,
  isScanning,
  scanResult,
  originalImagePreview
}) {
  const fileInputRef = useRef(null);
  const videoRef = useRef(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [activeTab, setActiveTab] = useState('annotated'); // 'annotated' or 'warped'
  const [samples, setSamples] = useState([]);
  const [isCameraActive, setIsCameraActive] = useState(false);
  const [cameraStream, setCameraStream] = useState(null);

  // Load sample photos from backend
  useEffect(() => {
    fetch('/api/samples')
      .then((res) => res.json())
      .then((data) => {
        if (data.samples) setSamples(data.samples);
      })
      .catch(() => {});
  }, []);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      onImageSelected(e.target.files[0]);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onImageSelected(e.dataTransfer.files[0]);
    }
  };

  const handleSelectSample = async (sample) => {
    try {
      const res = await fetch(sample.image);
      const blob = await res.blob();
      const file = new File([blob], sample.name, { type: 'image/png' });
      onImageSelected(file);
    } catch (err) {
      console.error('Failed to load sample image:', err);
    }
  };

  // Start Camera
  const handleStartCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' }
      });
      setCameraStream(stream);
      setIsCameraActive(true);
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    } catch (err) {
      alert('Unable to access camera: ' + err.message);
    }
  };

  // Capture Photo
  const handleCapturePhoto = () => {
    if (!videoRef.current) return;
    const canvas = document.createElement('canvas');
    canvas.width = videoRef.current.videoWidth || 640;
    canvas.height = videoRef.current.videoHeight || 480;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);

    canvas.toBlob((blob) => {
      if (blob) {
        const file = new File([blob], 'camera_capture.png', { type: 'image/png' });
        handleStopCamera();
        onImageSelected(file);
      }
    }, 'image/png');
  };

  // Stop Camera
  const handleStopCamera = () => {
    if (cameraStream) {
      cameraStream.getTracks().forEach((track) => track.stop());
      setCameraStream(null);
    }
    setIsCameraActive(false);
  };

  return (
    <div className="glass-panel" style={{ padding: '1.5rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h2 style={{ fontSize: '1.15rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <ImageIcon size={20} color="#38bdf8" /> Sudoku Image Input
        </h2>
        <button
          className="preset-chip"
          style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}
          onClick={isCameraActive ? handleStopCamera : handleStartCamera}
        >
          <Camera size={14} /> {isCameraActive ? 'Close Camera' : 'Use Camera'}
        </button>
      </div>

      {/* Live Camera Viewfinder */}
      {isCameraActive && (
        <div style={{ marginBottom: '1rem', position: 'relative', borderRadius: '12px', overflow: 'hidden', background: '#000' }}>
          <video
            ref={videoRef}
            autoPlay
            playsInline
            style={{ width: '100%', maxHeight: '320px', display: 'block', objectFit: 'cover' }}
          />
          <div style={{ position: 'absolute', bottom: '12px', left: '0', right: '0', display: 'flex', justifyContent: 'center' }}>
            <button className="btn btn-emerald" onClick={handleCapturePhoto}>
              <Camera size={18} /> Snap & Scan
            </button>
          </div>
        </div>
      )}

      {/* Upload Dropzone */}
      {!isCameraActive && (
        <div
          className={`upload-dropzone ${isDragOver ? 'drag-active' : ''}`}
          onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
          onDragLeave={() => setIsDragOver(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            type="file"
            ref={fileInputRef}
            style={{ display: 'none' }}
            accept="image/*"
            onChange={handleFileChange}
          />
          <Upload size={32} style={{ margin: '0 auto 0.75rem', color: '#60a5fa' }} />
          <p style={{ fontWeight: 600, color: '#f8fafc', marginBottom: '0.25rem' }}>
            {isScanning ? 'Processing image through vision pipeline...' : 'Click or drag & drop Sudoku photo'}
          </p>
          <span style={{ fontSize: '0.8rem', color: '#64748b' }}>
            Supports PNG, JPG, JPEG (handles perspective skew & angles)
          </span>
        </div>
      )}

      {/* 1-Click Sample Photos */}
      {samples.length > 0 && (
        <div style={{ marginTop: '1rem' }}>
          <span style={{ fontSize: '0.78rem', fontWeight: 600, color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '0.3rem', marginBottom: '0.5rem' }}>
            <Sparkles size={13} color="#f59e0b" /> Quick 1-Click Test Photos:
          </span>
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            {samples.map((s) => (
              <button
                key={s.name}
                className="preset-chip"
                style={{ fontSize: '0.78rem' }}
                onClick={() => handleSelectSample(s)}
              >
                📷 {s.label} Photo
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Vision Pipeline Overlays */}
      {scanResult && scanResult.images && (
        <div style={{ marginTop: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#94a3b8' }}>
              Vision Pipeline Outputs
            </span>
            <div style={{ display: 'flex', gap: '0.25rem' }}>
              <button
                className={`preset-chip ${activeTab === 'annotated' ? 'selected' : ''}`}
                style={{
                  background: activeTab === 'annotated' ? '#2563eb' : '#1e293b',
                  color: activeTab === 'annotated' ? '#fff' : '#94a3b8'
                }}
                onClick={() => setActiveTab('annotated')}
              >
                Photo Perspective
              </button>
              <button
                className={`preset-chip ${activeTab === 'warped' ? 'selected' : ''}`}
                style={{
                  background: activeTab === 'warped' ? '#2563eb' : '#1e293b',
                  color: activeTab === 'warped' ? '#fff' : '#94a3b8'
                }}
                onClick={() => setActiveTab('warped')}
              >
                Warped Grid
              </button>
            </div>
          </div>

          <div className="preview-container">
            <img
              src={
                activeTab === 'annotated'
                  ? scanResult.images.original_annotated
                  : scanResult.images.warped_annotated
              }
              alt="Detected Sudoku Grid"
              className="preview-img"
            />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.75rem', fontSize: '0.85rem' }}>
            {scanResult.is_valid ? (
              <span style={{ color: '#34d399', display: 'flex', alignItems: 'center', gap: '0.3rem', fontWeight: 600 }}>
                <CheckCircle size={16} /> Grid extracted, perspective corrected & reconstructed
              </span>
            ) : (
              <span style={{ color: '#f87171', display: 'flex', alignItems: 'center', gap: '0.3rem', fontWeight: 600 }}>
                <AlertCircle size={16} /> {scanResult.validation_errors?.[0] || 'Verification warnings'}
              </span>
            )}
          </div>
        </div>
      )}

      {/* Fallback preview while processing */}
      {!scanResult && originalImagePreview && (
        <div className="preview-container" style={{ marginTop: '1rem' }}>
          <img src={originalImagePreview} alt="Uploaded preview" className="preview-img" />
          {isScanning && (
            <div style={{
              position: 'absolute',
              inset: 0,
              background: 'rgba(11, 15, 25, 0.75)',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.75rem'
            }}>
              <div style={{ fontSize: '1.2rem', animation: 'spin 1s linear infinite' }}>⏳</div>
              <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>Detecting grid & recognizing digits...</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
