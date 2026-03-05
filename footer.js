(function () {
  // Derive the GitHub file path from the current URL
  let path = window.location.pathname.replace(/^\//, '') || 'index.html';
  if (path.endsWith('/')) path += 'index.html';
  if (!path.includes('.')) path += '.html'; // bare slug → slug.html

  const base = 'https://github.com/andyreagan/tools/blob/main/';
  const hist = 'https://github.com/andyreagan/tools/commits/main/';
  const api  = 'https://api.github.com/repos/andyreagan/tools/commits?path=' +
                encodeURIComponent(path) + '&per_page=1';

  const footer = document.createElement('footer');
  footer.style.cssText =
    'width:100%;box-sizing:border-box;font-family:system-ui,sans-serif;' +
    'font-size:12px;text-align:center;padding:1.5rem 1rem;' +
    'background:transparent;color:#999;border-top:1px solid #ddd;margin-top:2rem;' +
    'position:relative;z-index:1;';

  const updatedSpan = document.createElement('span');
  updatedSpan.id = 'footer-updated';

  footer.innerHTML =
    '<a href="/" style="color:#666;text-decoration:none;">Home</a>' +
    ' &nbsp;&middot;&nbsp; ' +
    '<a href="' + base + path + '" style="color:#666;text-decoration:none;">View source</a>' +
    ' &nbsp;&middot;&nbsp; ' +
    '<a href="' + hist + path + '" style="color:#666;text-decoration:none;">Changes</a>';
  footer.appendChild(document.createTextNode('\u00a0\u00a0\u00b7\u00a0\u00a0'));
  footer.appendChild(updatedSpan);

  document.body.appendChild(footer);

  // Fetch last commit date for this file
  fetch(api)
    .then(function (r) { return r.json(); })
    .then(function (data) {
      if (data && data[0] && data[0].commit && data[0].commit.author) {
        var iso = data[0].commit.author.date;
        var d = new Date(iso);
        var formatted = d.toLocaleDateString('en-US', {
          year: 'numeric', month: 'short', day: 'numeric'
        });
        updatedSpan.textContent = 'Last updated ' + formatted;
      }
    })
    .catch(function () {
      // silently ignore — network or rate-limit errors
    });
})();
