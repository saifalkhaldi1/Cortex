import React, { useRef, useEffect } from "react";
import styles from "./Visualizer.module.css";

export const STATUS = {
  IDLE: "idle",
  LISTENING: "listening",
  SPEAKING: "speaking",
};

export default function AiVisualizer({ status = STATUS.IDLE }) {
  const canvasRef = useRef(null);
  const statusRef = useRef(status);
  useEffect(() => {
    statusRef.current = status;
  }, [status]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    let w = (canvas.width = canvas.offsetWidth);
    let h = (canvas.height = canvas.offsetHeight);
    const NUM = 80;
    let particles = [];

    function init() {
      w = canvas.width = canvas.offsetWidth;
      h = canvas.height = canvas.offsetHeight;
      particles = Array.from({ length: NUM }, () => ({
        x: Math.random() * w,
        y: Math.random() * h,
        vx: (Math.random() - 0.5),
        vy: (Math.random() - 0.5),
        r: Math.random() * 2 + 1,
      }));
    }

    function draw() {
      ctx.clearRect(0, 0, w, h);
      const color = getComputedStyle(document.documentElement)
        .getPropertyValue("--primary-color")
        .trim();
      const st = statusRef.current;
      let alpha, speed;
      if (st === STATUS.SPEAKING) { alpha = 1;   speed = 1.8; }
      else if (st === STATUS.LISTENING) { alpha = 0.8; speed = 1.2; }
      else { alpha = 0.5; speed = 0.6; }

      ctx.globalAlpha = alpha;
      particles.forEach((p) => {
        p.x += p.vx * speed;
        p.y += p.vy * speed;
        if (p.x < 0 || p.x > w) p.vx *= -1;
        if (p.y < 0 || p.y > h) p.vy *= -1;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();
      });
      requestAnimationFrame(draw);
    }

    init();
    draw();
    window.addEventListener("resize", init);
    return () => window.removeEventListener("resize", init);
  }, []);

  return (
    <div className={styles.orbContainer}>
      <canvas ref={canvasRef} className={styles.canvas} />
    </div>
  );
}
