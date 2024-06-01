class WebRTCInterface {
    constructor() {
        this.peers = {};
        this.localConnection = null;
        this.dataChannel = null;
        this.onMessageCallback = null;
        this.socket = new WebSocket(`ws://${window.location.host}/ws`);
        
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
        this.localConnection = new RTCPeerConnection({
            iceServers: [
                { urls: 'stun:stun.l.google.com:19302' },
            ],
        });

        this.dataChannel = this.localConnection.createDataChannel('chat');
        this.dataChannel.onmessage = (event) => {
            if (this.onMessageCallback) {
                this.onMessageCallback(JSON.parse(event.data));
            }
        };

        this.localConnection.onicecandidate = (event) => {
            if (event.candidate) {
                this.socket.send(JSON.stringify({
                    type: 'ice-candidate',
                    target: clientId,
                    candidate: event.candidate,
                }));
            }
        };

        this.localConnection.ondatachannel = (event) => {
            event.channel.onmessage = (msgEvent) => {
                if (this.onMessageCallback) {
                    this.onMessageCallback(JSON.parse(msgEvent.data));
                }
            };
        };

        const offer = await this.localConnection.createOffer();
        await this.localConnection.setLocalDescription(offer);

        this.socket.send(JSON.stringify({
            type: 'offer',
            target: clientId,
            sdp: this.localConnection.localDescription,
        }));

        this.peers[clientId] = this.localConnection;
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
        // This function is called to initialize the WebSocket connection and to wait for peer connection initialization.
        // Additional code to wait until peer connections are established can be added here if necessary.
        // Currently assuming that `initializePeers` will handle this asynchronously as messages are received.
    }

    broadcast(msg) {
        const messageStr = JSON.stringify(msg);
        for (let peer of Object.values(this.peers)) {
            peer.dataChannels.forEach(channel => {
                channel.send(messageStr);
            });
        }
    }

    setOnMessageCallback(callback) {
        this.onMessageCallback = callback;
    }
}
