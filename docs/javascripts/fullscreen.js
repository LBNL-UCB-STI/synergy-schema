(() => {
  function initMermaidFullscreen() {
    document.querySelectorAll('.mermaid').forEach((mermaidEl) => {
      if (mermaidEl.closest('.mermaid-container')) return;

      const container = document.createElement('div');
      container.className = 'mermaid-container';
      mermaidEl.parentNode.insertBefore(container, mermaidEl);
      container.appendChild(mermaidEl);

      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'mermaid-fullscreen-btn';
      btn.setAttribute('aria-label', 'Toggle fullscreen');
      btn.innerHTML = '⛶ Fullscreen';
      btn.onclick = () => {
        if (!document.fullscreenElement) {
          if (container.requestFullscreen) {
            container.requestFullscreen();
          } else if (container.webkitRequestFullscreen) {
            container.webkitRequestFullscreen();
          }
        } else {
          if (document.exitFullscreen) {
            document.exitFullscreen();
          }
        }
      };
      container.appendChild(btn);
    });
  }

  document.addEventListener('fullscreenchange', () => {
    const isFs = !!document.fullscreenElement;
    document.querySelectorAll('.mermaid-fullscreen-btn').forEach((btn) => {
      btn.innerHTML = isFs ? '✕ Exit' : '⛶ Fullscreen';
    });
  });

  if (typeof document$ !== 'undefined') {
    document$.subscribe(initMermaidFullscreen);
  } else if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initMermaidFullscreen);
  } else {
    initMermaidFullscreen();
  }

  setInterval(initMermaidFullscreen, 500);
})();
