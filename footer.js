(function () {
  // Derive the GitHub file path from the current URL
  let path = window.location.pathname.replace(/^\//, '') || 'index.html';
  if (path.endsWith('/')) path += 'index.html';
  if (!path.includes('.')) path += '.html'; // bare slug → slug.html

  const base = 'https://github.com/andyreagan/tools/blob/main/';
  const hist = 'https://github.com/andyreagan/tools/commits/main/';

  const footer = document.createElement('footer');
  footer.style.cssText =
    'width:100%;box-sizing:border-box;font-family:system-ui,sans-serif;' +
    'font-size:12px;text-align:center;padding:1.5rem 1rem;' +
    'border-top:1px solid currentColor;margin-top:2rem;opacity:0.6;';
  footer.innerHTML =
    '<a href="/">Home</a> &nbsp;&middot;&nbsp; ' +
    '<a href="' + base + path + '">View source</a> &nbsp;&middot;&nbsp; ' +
    '<a href="' + hist + path + '">Changes</a>';

  document.body.appendChild(footer);
})();
