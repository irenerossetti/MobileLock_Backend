import os
import logging
from web3 import Web3

logger = logging.getLogger(__name__)

class BlockchainService:
    def __init__(self):
        # En un escenario real, esto vendría de variables de entorno
        # POLYGON_RPC_URL="https://polygon-rpc.com"
        # SERVER_PRIVATE_KEY="0x..."
        
        self.rpc_url = os.getenv("POLYGON_RPC_URL", "https://polygon-rpc.com")
        self.private_key = os.getenv("SERVER_PRIVATE_KEY")
        self.contract_address = os.getenv("CONTRACT_ADDRESS")
        
        # Conectar a Polygon (o la red especificada)
        try:
            self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        except Exception as e:
            logger.error(f"Error conectando a Web3: {e}")
            self.w3 = None

    def registrar_dispositivo(self, imei_hash, estado):
        """
        Registra el estado de un dispositivo en la blockchain.
        Retorna el hash de la transacción si es exitoso, o None en caso de error.
        """
        if not self.w3 or not self.w3.is_connected():
            logger.warning("No hay conexión con la red Blockchain.")
            return self._mock_tx_hash(imei_hash, estado)

        if not self.private_key:
            logger.warning("SERVER_PRIVATE_KEY no configurada. Simulando registro en Blockchain.")
            return self._mock_tx_hash(imei_hash, estado)

        try:
            # Configurar cuenta desde llave privada
            account = self.w3.eth.account.from_key(self.private_key)
            
            # NOTA: Como no tenemos el ABI del contrato real en este punto,
            # este código es ilustrativo y utiliza una llamada genérica o se salta si no hay contrato.
            if not self.contract_address:
                logger.warning("CONTRACT_ADDRESS no configurada. Simulando registro.")
                return self._mock_tx_hash(imei_hash, estado)

            # --- CÓDIGO REAL COMENTADO ---
            # contract = self.w3.eth.contract(address=self.contract_address, abi=CONTRACT_ABI)
            # nonce = self.w3.eth.get_transaction_count(account.address)
            # 
            # tx = contract.functions.registerDevice(
            #     imei_hash, estado
            # ).build_transaction({
            #     'chainId': 137, # Polygon Mainnet
            #     'gas': 2000000,
            #     'gasPrice': self.w3.eth.gas_price,
            #     'nonce': nonce,
            # })
            # 
            # signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            # tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            # return self.w3.to_hex(tx_hash)

            return self._mock_tx_hash(imei_hash, estado)

        except Exception as e:
            logger.error(f"Error firmando/enviando transacción a Blockchain: {e}")
            return None

    def _mock_tx_hash(self, imei_hash, estado):
        import hashlib
        import time
        raw = f"{imei_hash}-{estado}-{time.time()}"
        mock_hash = "0x" + hashlib.sha256(raw.encode()).hexdigest()
        logger.info(f"Registro Blockchain Simulado. TxHash: {mock_hash}")
        return mock_hash
