// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title MobileLock
 * @dev Contrato inteligente para registrar la propiedad, estado de seguridad y huella visual de dispositivos móviles.
 */
contract MobileLock {
    
    struct Dispositivo {
        string visualHash;
        address ownerAddress;
        bool isStolen;
        uint256 registrationTimestamp;
    }

    // Mapeo de hash_imei -> Detalle del dispositivo
    mapping(string => Dispositivo) private dispositivos;
    
    // Mapeo auxiliar para verificar si un IMEI ya está registrado
    mapping(string => bool) private registrado;

    // Eventos para el rastreo y auditoría en la blockchain
    event DeviceRegistered(
        string indexed imeiHash, 
        string visualHash, 
        address indexed ownerAddress, 
        uint256 timestamp
    );
    
    event DeviceStatusChanged(
        string indexed imeiHash, 
        bool isStolen, 
        string motivo, 
        uint256 timestamp
    );
    
    event DeviceTransferred(
        string indexed imeiHash, 
        address indexed oldOwner, 
        address indexed newOwner, 
        uint256 timestamp
    );

    // Modificadores de acceso
    modifier onlyDeviceOwner(string memory _imeiHash) {
        require(dispositivos[_imeiHash].ownerAddress == msg.sender, "No eres el propietario registrado de este dispositivo.");
        _;
    }

    modifier deviceExists(string memory _imeiHash) {
        require(registrado[_imeiHash], "El dispositivo con este IMEI no esta registrado.");
        _;
    }

    /**
     * @notice Registra un nuevo dispositivo móvil en la blockchain.
     * @param _imeiHash El hash único del IMEI del dispositivo.
     * @param _visualHash El hash visual único generado por la IA (EfficientNet).
     */
    function registerDevice(string memory _imeiHash, string memory _visualHash) public {
        require(!registrado[_imeiHash], "El dispositivo ya se encuentra registrado en la blockchain.");
        require(bytes(_imeiHash).length > 0, "El hash del IMEI no puede estar vacio.");
        require(bytes(_visualHash).length > 0, "El hash visual de la IA no puede estar vacio.");

        dispositivos[_imeiHash] = Dispositivo({
            visualHash: _visualHash,
            ownerAddress: msg.sender,
            isStolen: false,
            registrationTimestamp: block.timestamp
        });

        registrado[_imeiHash] = true;

        emit DeviceRegistered(_imeiHash, _visualHash, msg.sender, block.timestamp);
    }

    /**
     * @notice Reporta un dispositivo registrado como ROBADO o EXTRAVIADO.
     * @param _imeiHash El hash único del IMEI del dispositivo.
     * @param _motivo Descripcion o motivo del reporte de robo.
     */
    function reportStolen(string memory _imeiHash, string memory _motivo) 
        public 
        deviceExists(_imeiHash) 
        onlyDeviceOwner(_imeiHash) 
    {
        require(!dispositivos[_imeiHash].isStolen, "El dispositivo ya esta reportado como robado.");

        dispositivos[_imeiHash].isStolen = true;

        emit DeviceStatusChanged(_imeiHash, true, _motivo, block.timestamp);
    }

    /**
     * @notice Reporta un dispositivo previamente robado como RECUPERADO / LIBRE.
     * @param _imeiHash El hash único del IMEI del dispositivo.
     */
    function reportRecovered(string memory _imeiHash) 
        public 
        deviceExists(_imeiHash) 
        onlyDeviceOwner(_imeiHash) 
    {
        require(dispositivos[_imeiHash].isStolen, "El dispositivo no esta reportado como robado.");

        dispositivos[_imeiHash].isStolen = false;

        emit DeviceStatusChanged(_imeiHash, false, "Dispositivo recuperado", block.timestamp);
    }

    /**
     * @notice Transfiere la propiedad del dispositivo a un nuevo propietario.
     * @param _imeiHash El hash único del IMEI del dispositivo.
     * @param _newOwner La direccion de Ethereum/Polygon del nuevo propietario.
     */
    function transferDevice(string memory _imeiHash, address _newOwner) 
        public 
        deviceExists(_imeiHash) 
        onlyDeviceOwner(_imeiHash) 
    {
        require(_newOwner != address(0), "La direccion del nuevo propietario no es valida.");
        require(_newOwner != msg.sender, "No puedes transferir el dispositivo a ti mismo.");
        require(!dispositivos[_imeiHash].isStolen, "No se puede transferir un dispositivo con reporte de robo activo.");

        address oldOwner = dispositivos[_imeiHash].ownerAddress;
        dispositivos[_imeiHash].ownerAddress = _newOwner;

        emit DeviceTransferred(_imeiHash, oldOwner, _newOwner, block.timestamp);
    }

    /**
     * @notice Obtiene la informacion de registro completa de un dispositivo.
     * @param _imeiHash El hash único del IMEI a consultar.
     */
    function getDevice(string memory _imeiHash) 
        public 
        view 
        deviceExists(_imeiHash) 
        returns (
            string memory visualHash,
            address ownerAddress,
            bool isStolen,
            uint256 registrationTimestamp
        ) 
    {
        Dispositivo memory dev = dispositivos[_imeiHash];
        return (dev.visualHash, dev.ownerAddress, dev.isStolen, dev.registrationTimestamp);
    }
}
