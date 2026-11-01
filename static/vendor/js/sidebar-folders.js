document.addEventListener('DOMContentLoaded', () => {
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function initSidebarFolders() {
    document.querySelectorAll('.sidebar-folder').forEach(folder => {
      const btn = folder.querySelector('.folder-header');
      const contents = folder.querySelector('.folder-contents');
      if (!btn || !contents) return;

      if (document.body.classList.contains('sin-animaciones') || reduceMotion) {
        contents.style.transition = 'none';
      } else {
        contents.style.transition = 'max-height 320ms cubic-bezier(0.2,0.8,0.2,1)';
      }

      contents.style.overflow = 'hidden';
      contents.style.maxHeight = '0px';

      function openFolder() {
        folder.classList.add('open');
        btn.setAttribute('aria-expanded', 'true');
        const full = contents.scrollHeight;
        contents.style.maxHeight = full + 'px';

        const tidy = () => {
          if (folder.classList.contains('open')) {
            contents.style.maxHeight = 'none';
          }
          contents.removeEventListener('transitionend', tidy);
        };
        contents.addEventListener('transitionend', tidy);
      }

      function closeFolder() {
        const current = contents.scrollHeight;
        contents.style.maxHeight = current + 'px';
        contents.offsetHeight;
        folder.classList.remove('open');
        btn.setAttribute('aria-expanded', 'false');
        requestAnimationFrame(() => { contents.style.maxHeight = '0px'; });
      }

      btn.addEventListener('click', (e) => {
        if (btn.classList.contains('disabled')) {
          return; // locked section
        }
        e.preventDefault();
        e.stopPropagation();
        if (folder.classList.contains('open')) closeFolder();
        else openFolder();
      });

      window.addEventListener('resize', () => {
        if (folder.classList.contains('open')) {
          contents.style.maxHeight = contents.scrollHeight + 'px';
        }
      });
    });
  }

  requestAnimationFrame(() => setTimeout(initSidebarFolders, 30));
});
