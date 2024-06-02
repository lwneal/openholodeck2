const maxLines = 60;
const consoleElId = 'console';

function ensureConsoleElement() {
    let consoleEl = document.getElementById(consoleElId);
    if (!consoleEl) {
        consoleEl = document.createElement('div');
        consoleEl.id = consoleElId;
        consoleEl.style.color = 'white';
        consoleEl.style.backgroundColor = 'black';
        consoleEl.style.width = '100%';
        consoleEl.style.height = '480px';
        consoleEl.style.overflowY = 'scroll';
        document.body.appendChild(consoleEl);
    }
    return consoleEl;
}

function log(...args) {
    let message = args.join(' ');
    console.log(message);

    let timestamp = new Date().toISOString().substr(11, 8);
    let consoleEl = ensureConsoleElement();

    let line = document.createElement('pre');
    line.innerText = `[${timestamp}] ${message}`;
    consoleEl.appendChild(line);

    while (consoleEl.childNodes.length > maxLines) {
        consoleEl.removeChild(consoleEl.firstChild);
    }
    consoleEl.scrollTop = consoleEl.scrollHeight;
}

export { log };
