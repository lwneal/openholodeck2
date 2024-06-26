class WebRTCInterface {
    constructor() {
        this.peers = {};
        this.localConnections = {};
        this.dataChannels = {};
        this.onMessageCallback = null;
        let proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
        this.socket = new WebSocket(`${proto}://${window.location.host}/ws`);
        
        this.socket.addEventListener('message', async (event) => {
            const message = JSON.parse(event.data);
            if (message.type === 'client_id') {
                this.clientId = message.id;
            } else if (message.type === 'clients') {
                await this.initializePeers(message.clients);
            } else if (message.type === 'offer') {
                await this.handleOffer(message);
            } else if (message.type === 'answer') {
                await this.handleAnswer(message);
            } else if (message.type === 'ice-candidate') {
                await this.handleIceCandidate(message);
            }
        });
    }

    connected() {
        return Object.keys(this.peers).length > 0;
    }

    async initializePeers(clients) {
        for (let client of clients) {
            if (client.id !== this.clientId && !this.peers[client.id]) {
                await this.createPeerConnection(client.id);
            }
        }
    }

    async createPeerConnection(clientId) {
        const localConnection = new RTCPeerConnection({
            iceServers: [
                { urls: 'stun:stun.l.google.com:19302' },
            ],
        });

        const dataChannel = localConnection.createDataChannel('chat');
        dataChannel.onmessage = (event) => {
            if (this.onMessageCallback) {
                this.onMessageCallback(JSON.parse(event.data));
            }
        };

        localConnection.onicecandidate = (event) => {
            if (event.candidate) {
                this.socket.send(JSON.stringify({
                    type: 'ice-candidate',
                    target: clientId,
                    candidate: event.candidate,
                }));
            }
        };

        localConnection.ondatachannel = (event) => {
            event.channel.onmessage = (msgEvent) => {
                if (this.onMessageCallback) {
                    this.onMessageCallback(JSON.parse(msgEvent.data));
                }
            };
        };

        const offer = await localConnection.createOffer();
        await localConnection.setLocalDescription(offer);

        this.socket.send(JSON.stringify({
            type: 'offer',
            target: clientId,
            sdp: localConnection.localDescription,
            clientId: this.clientId,
        }));

        this.localConnections[clientId] = localConnection;
        this.dataChannels[clientId] = dataChannel;
        this.peers[clientId] = localConnection;
    }

    async handleOffer(message) {
        const remoteConnection = new RTCPeerConnection({
            iceServers: [
                { urls: 'stun:stun.l.google.com:19302' },
            ],
        });

        remoteConnection.onicecandidate = (event) => {
            if (event.candidate) {
                this.socket.send(JSON.stringify({
                    type: 'ice-candidate',
                    target: message.clientId,
                    candidate: event.candidate,
                }));
            }
        };

        remoteConnection.ondatachannel = (event) => {
            event.channel.onmessage = (msgEvent) => this.onMessageCallback(JSON.parse(msgEvent.data));
        };

        await remoteConnection.setRemoteDescription(new RTCSessionDescription(message.sdp));
        const answer = await remoteConnection.createAnswer();
        await remoteConnection.setLocalDescription(answer);

        this.socket.send(JSON.stringify({
            type: 'answer',
            target: message.clientId,
            sdp: remoteConnection.localDescription,
        }));

        this.dataChannels[message.clientId] = remoteConnection.createDataChannel('chat');
        this.peers[message.clientId] = remoteConnection;
    }

    async handleAnswer(message) {
        const connection = this.peers[message.clientId];
        if (connection) {
            await connection.setRemoteDescription(new RTCSessionDescription(message.sdp));
        }
    }

    async handleIceCandidate(message) {
        const connection = this.peers[message.clientId];
        if (connection) {
            await connection.addIceCandidate(new RTCIceCandidate(message.candidate));
        }
    }

    async connect() {
        // Assuming that `initializePeers` will handle this asynchronously as messages are received.
    }

    broadcast(msg) {
        const messageStr = JSON.stringify(msg);
        for (let channel of Object.values(this.dataChannels)) {
            channel.send(messageStr);
        }
    }

    setOnMessageCallback(callback) {
        this.onMessageCallback = callback;
    }
}
