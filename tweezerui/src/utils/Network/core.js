class ServerConfig {
    constructor() {
        this.config = {
            mainServer: {
                host: '10.0.63.153',
                port: 3001
            },
        };
    }

   getMainServerHost() {
        return this.config.mainServer.host;
    }

    getMainServerPort() {
        return this.config.mainServer.port;
    }

    getMainServerUrl() {
        return `http://${this.getMainServerHost()}:${this.getMainServerPort()}`;
    }
}


export default new ServerConfig();