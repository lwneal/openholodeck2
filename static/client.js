import { log } from './consoleLog.js';
let ws, pc, dataChannel;

function setupWebSocket() {
    log('setupWebSocket()');
    let proto = location.protocol === 'https:' ? 'wss' : 'ws';
    ws = new WebSocket(proto + '://' + location.host + '/ws');
    
    ws.onopen = () => {
        log('WebSocket connection opened');
        createConnection();
    };

    ws.onmessage = async event => {
        const message = JSON.parse(event.data);

        if (message.sdp) {
            await pc.setRemoteDescription(new RTCSessionDescription(message.sdp));
            if (message.sdp.type === 'offer') {
                const answer = await pc.createAnswer();
                await pc.setLocalDescription(answer);
                ws.send(JSON.stringify({ 'sdp': pc.localDescription }));
            }
        } else if (message.candidate) {
            try {
                await pc.addIceCandidate(new RTCIceCandidate(message.candidate));
            } catch (e) {
                log('Error adding received ice candidate', e);
            }
        }
    };

    ws.onclose = () => {
        log('WebSocket connection closed, retrying...');
        setTimeout(setupWebSocket, 1000);
    };

    ws.onerror = error => {
        log('WebSocket error: ' + error.message);
        ws.close();
    };
}

async function createConnection() {
    log('createConnection()');
    pc = new RTCPeerConnection({
        iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
    });

    pc.onicecandidate = event => {
        if (event.candidate) {
            ws.send(JSON.stringify({ 'candidate': event.candidate }));
        }
    };

    pc.ondatachannel = event => {
        dataChannel = event.channel;
        setupDataChannel();
    };

    try {
        dataChannel = pc.createDataChannel('chat');
        setupDataChannel();

        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);
        ws.send(JSON.stringify({ 'sdp': pc.localDescription }));
    } catch (e) {
        log('Failed to create offer:', e);
    }
}

function setupDataChannel() {
    log('setupDataChannel()');
    dataChannel.onopen = () => {
        log('Data Channel Opened');
        setInterval(() => {
            let msg = `Time: ${new Date().toLocaleTimeString()} User Agent: ${navigator.userAgent}`;
            const message = JSON.stringify({ 'content': msg });
            if (dataChannel.readyState === 'open') {
                dataChannel.send(message);
            }
        }, 3000);
    };

    dataChannel.onmessage = (event) => {
        const message = JSON.parse(event.data);
        log(`Received: ${message.content}`);
    };

    dataChannel.onclose = () => {
        log('Data Channel Closed');
    };

    dataChannel.onerror = (error) => {
        log('Data Channel Error: ' + error.message);
    };
}

setupWebSocket();
