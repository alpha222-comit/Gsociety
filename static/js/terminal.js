const commandInput = document.getElementById('command');
const outputDiv = document.getElementById('output');
const typeSound = document.getElementById('type-sound');

let history = [];
let historyIndex = 0;

commandInput.addEventListener('keydown', (e) => {
    if (e.key === "Enter") {
        let cmd = commandInput.value.trim();
        history.push(cmd);
        historyIndex = history.length;

        outputDiv.innerHTML += `<div><span class="user">root@genesis:~$</span> ${cmd}</div>`;
        processCommand(cmd.toLowerCase());
        commandInput.value = '';
        outputDiv.scrollTop = outputDiv.scrollHeight;
    } else if (e.key === 'ArrowUp') {
        if (historyIndex > 0) {
            historyIndex--;
            commandInput.value = history[historyIndex];
        }
    } else if (e.key === 'ArrowDown') {
        if (historyIndex < history.length - 1) {
            historyIndex++;
            commandInput.value = history[historyIndex];
        } else {
            commandInput.value = '';
        }
    } else {
        typeSound.currentTime = 0;
        typeSound.play();
    }
});

function processCommand(cmd) {
    switch (cmd) {
        case 'help':
            output('Available commands: help, clear, whoami, ifconfig, ls, nmap, sudo, history');
            break;
        case 'clear':
            outputDiv.innerHTML = '';
            break;
        case 'whoami':
            output('root');
            break;
        case 'ls':
            output('projects/  secrets.txt  exploit.py  payloads/');
            break;
        case 'nmap':
            output('Starting Nmap scan...\nHost is up (127.0.0.1)\nOpen ports: 22/tcp ssh, 80/tcp http');
            break;
        case 'ifconfig':
            output('eth0: inet 192.168.1.100  netmask 255.255.255.0  broadcast 192.168.1.255');
            break;
        case 'sudo':
            output('Permission denied: you are not in the sudoers file.');
            break;
        case 'history':
            output(history.join('\n'));
            break;
        default:
            output(`Command not found: ${cmd}`);
    }
}

function output(text) {
    outputDiv.innerHTML += `<pre>${text}</pre>`;
}
