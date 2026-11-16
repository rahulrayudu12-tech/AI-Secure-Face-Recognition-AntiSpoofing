/**
 * AuraID Real-time Biometric Scanner & HUD Visualizer
 */
class AuraWebcamScanner {
  constructor(options = {}) {
    this.videoElement = document.getElementById(options.videoId || 'webcamVideo');
    this.canvasElement = document.getElementById(options.canvasId || 'webcamCanvas');
    this.ctx = this.canvasElement ? this.canvasElement.getContext('2d') : null;
    this.stream = null;
    this.isScanning = false;
    this.scanInterval = null;
    this.selectedAttack = null;
    this.targetUserId = null;
    this.fps = options.fps || 4; // 4 FPS for smooth AI processing without network overload
    this.onResultCallback = options.onResult || null;
  }

  async startCamera() {
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: 'user'
        },
        audio: false
      });
      this.videoElement.srcObject = this.stream;
      await this.videoElement.play();
      this.isScanning = true;
      this.startFrameLoop();
      return { success: true };
    } catch (err) {
      console.warn("Webcam access error:", err);
      return { 
        success: false, 
        message: "Camera permission denied or camera not found. You can also upload test photos." 
      };
    }
  }

  stopCamera() {
    this.isScanning = false;
    if (this.scanInterval) {
      clearInterval(this.scanInterval);
      this.scanInterval = null;
    }
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
      this.stream = null;
    }
    if (this.ctx && this.canvasElement) {
      this.ctx.clearRect(0, 0, this.canvasElement.width, this.canvasElement.height);
    }
  }

  setAttackSimulation(attackType) {
    this.selectedAttack = attackType;
  }

  setTargetUser(userId) {
    this.targetUserId = userId;
  }

  startFrameLoop() {
    if (this.scanInterval) clearInterval(this.scanInterval);

    this.scanInterval = setInterval(() => {
      if (!this.isScanning || !this.videoElement || this.videoElement.readyState !== 4) return;
      this.captureAndAuthenticate();
    }, 1000 / this.fps);
  }

  captureFrameAsBase64() {
    if (!this.videoElement || this.videoElement.videoWidth === 0) return null;
    const tempCanvas = document.createElement('canvas');
    tempCanvas.width = this.videoElement.videoWidth;
    tempCanvas.height = this.videoElement.videoHeight;
    const tempCtx = tempCanvas.getContext('2d');
    tempCtx.drawImage(this.videoElement, 0, 0);
    return tempCanvas.toDataURL('image/jpeg', 0.85);
  }

  async captureAndAuthenticate() {
    const base64Image = this.captureFrameAsBase64();
    if (!base64Image) return;

    try {
      const payload = {
        image: base64Image,
        user_id: this.targetUserId,
        simulate_attack: this.selectedAttack
      };

      const response = await fetch('/api/authenticate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await response.json();
      this.drawHUDOverlay(data);
      if (this.onResultCallback) {
        this.onResultCallback(data);
      }
    } catch (err) {
      console.error("Auth frame error:", err);
    }
  }

  drawHUDOverlay(data) {
    if (!this.ctx || !this.canvasElement || !this.videoElement) return;

    const w = this.videoElement.videoWidth || 640;
    const h = this.videoElement.videoHeight || 480;
    this.canvasElement.width = w;
    this.canvasElement.height = h;

    this.ctx.clearRect(0, 0, w, h);

    if (data && data.face_detected && data.box) {
      const [bx, by, bw, bh] = data.box;
      const decision = data.decision;
      const isGranted = decision === 'ACCESS_GRANTED';
      const isSpoof = decision === 'SPOOF_DETECTED';

      const strokeColor = isGranted ? '#10b981' : (isSpoof ? '#ef4444' : '#06b6d4');

      // Futuristic Bounding Box Corners
      const cLen = Math.min(25, bw * 0.25);
      this.ctx.lineWidth = 3;
      this.ctx.strokeStyle = strokeColor;
      this.ctx.shadowColor = strokeColor;
      this.ctx.shadowBlur = 12;

      // Top-Left
      this.ctx.beginPath();
      this.ctx.moveTo(bx, by + cLen);
      this.ctx.lineTo(bx, by);
      this.ctx.lineTo(bx + cLen, by);
      this.ctx.stroke();

      // Top-Right
      this.ctx.beginPath();
      this.ctx.moveTo(bx + bw - cLen, by);
      this.ctx.lineTo(bx + bw, by);
      this.ctx.lineTo(bx + bw, by + cLen);
      this.ctx.stroke();

      // Bottom-Left
      this.ctx.beginPath();
      this.ctx.moveTo(bx, by + bh - cLen);
      this.ctx.lineTo(bx, by + bh);
      this.ctx.lineTo(bx + cLen, by + bh);
      this.ctx.stroke();

      // Bottom-Right
      this.ctx.beginPath();
      this.ctx.moveTo(bx + bw - cLen, by + bh);
      this.ctx.lineTo(bx + bw, by + bh);
      this.ctx.lineTo(bx + bw, by + bh - cLen);
      this.ctx.stroke();

      // Draw Landmarks
      if (data.landmarks && Array.isArray(data.landmarks)) {
        this.ctx.fillStyle = '#22d3ee';
        data.landmarks.forEach(pt => {
          this.ctx.beginPath();
          this.ctx.arc(pt[0], pt[1], 3.5, 0, 2 * Math.PI);
          this.ctx.fill();
        });
      }

      // Floating Tag Label above face
      const userName = (data.user && data.user.name) ? data.user.name : "Unknown Subject";
      const badgeText = isGranted 
        ? `VERIFIED: ${userName} (${Math.round((data.identity_score || 0) * 100)}%)` 
        : (isSpoof ? `SPOOF ALERT: ${data.attack_type.toUpperCase()}` : `SUBJECT: ${userName}`);

      this.ctx.font = 'bold 13px Inter, sans-serif';
      const textWidth = this.ctx.measureText(badgeText).width;
      const tagX = Math.max(10, bx + bw / 2 - textWidth / 2 - 12);
      const tagY = Math.max(25, by - 12);

      this.ctx.fillStyle = 'rgba(15, 11, 36, 0.85)';
      this.ctx.fillRect(tagX, tagY - 18, textWidth + 24, 24);
      this.ctx.strokeRect(tagX, tagY - 18, textWidth + 24, 24);

      this.ctx.fillStyle = strokeColor;
      this.ctx.fillText(badgeText, tagX + 12, tagY - 2);
    }
  }
}

window.AuraWebcamScanner = AuraWebcamScanner;
