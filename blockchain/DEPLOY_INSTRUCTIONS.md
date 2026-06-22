# Guía de Despliegue del Smart Contract en Polygon Amoy

Esta guía te guiará paso a paso para compilar y desplegar el contrato inteligente [MobileLock.sol](file:///d:/Universidad/I-2026/Software_1/Proyecto_Grupal/Backend_proy_sw/MobileLock_Backend/blockchain/contracts/MobileLock.sol) en la red de pruebas **Polygon Amoy Testnet** utilizando **Remix IDE** y **MetaMask**.

---

## Paso 1: Configurar MetaMask para Polygon Amoy

Si aún no tienes configurada la red de pruebas **Polygon Amoy** en tu billetera MetaMask, agrégala con los siguientes parámetros:

1. Abre **MetaMask**.
2. Haz clic en el selector de redes (arriba a la izquierda) y selecciona **Agregar red** -> **Agregar una red manualmente**.
3. Rellena los campos con la siguiente configuración:
   * **Nombre de la red:** `Polygon Amoy Testnet`
   * **Nueva dirección URL de RPC:** `https://rpc-amoy.polygon.technology` (o una privada de Alchemy/Infura si la tienes)
   * **Identificador de cadena (Chain ID):** `80002`
   * **Símbolo de moneda:** `POL`
   * **Dirección URL del explorador de bloques:** `https://amoy.polygonscan.com/`
4. Haz clic en **Guardar**.

---

## Paso 2: Obtener Fondos de Prueba (POL/MATIC Faucets)

El despliegue del contrato requiere gas (comisión de red). Puedes obtener monedas de prueba (`POL`) gratuitas usando alguno de los siguientes grifos (Faucets):

1. **Polygon Faucet Oficial:** [faucet.polygon.technology](https://faucet.polygon.technology/)
   * Selecciona la red **Amoy** y el token **POL**.
   * Pega la dirección pública de tu cuenta de MetaMask y solicita la transferencia.
2. **Alchemy Amoy Faucet:** [alchemy.com/faucets/polygon-amoy](https://www.alchemy.com/faucets/polygon-amoy) (requiere cuenta gratuita en Alchemy).
3. **Chainlink Faucet:** [faucets.chain.link/polygon-amoy](https://faucets.chain.link/polygon-amoy).

---

## Paso 3: Cargar y Compilar en Remix IDE

1. Abre tu navegador e ingresa a [remix.ethereum.org](https://remix.ethereum.org/).
2. En la sección **File Explorer** (menú izquierdo), crea un nuevo archivo llamado `MobileLock.sol`.
3. Abre el archivo en Remix y copia e inserta todo el código del archivo local:
   [MobileLock.sol](file:///d:/Universidad/I-2026/Software_1/Proyecto_Grupal/Backend_proy_sw/MobileLock_Backend/blockchain/contracts/MobileLock.sol)
4. En el menú izquierdo de Remix, ve a la pestaña **Solidity Compiler** (el icono de Solidity).
5. Selecciona la versión del compilador `0.8.20` o superior.
6. Haz clic en **Compile MobileLock.sol**.

---

## Paso 4: Desplegar en la Red Polygon Amoy

1. En el menú izquierdo de Remix, ve a la pestaña **Deploy & Run Transactions** (el icono de Ethereum con flecha).
2. En el menú desplegable **Environment**, selecciona **Injected Provider - MetaMask**.
   * MetaMask se abrirá y te pedirá permiso para conectarse a Remix. Asegúrate de estar en la red **Polygon Amoy Testnet**.
3. Verifica que en el campo **Contract** esté seleccionado `MobileLock`.
4. Haz clic en el botón naranja **Deploy**.
5. Se abrirá MetaMask solicitando la confirmación de la transacción y el pago del gas en POL de prueba. Haz clic en **Confirmar**.
6. En la parte inferior de Remix (en la consola) y en el panel izquierdo bajo **Deployed Contracts**, verás tu contrato desplegado con éxito.

---

## Paso 5: Guardar los Datos Obtenidos

Una vez desplegado:
1. Copia la **dirección del contrato inteligente** (Contract Address) generada en Remix (puedes hacer clic en el botón de copiar junto al contrato en "Deployed Contracts").
2. Guarda el **ABI** del contrato (puedes copiar el JSON del ABI desde la pestaña del compilador haciendo clic en "ABI").
3. Configura estos valores en el archivo `.env` del backend Django:
   * `BLOCKCHAIN_CONTRACT_ADDRESS=<DIRECCION_DE_TU_CONTRATO>`
   * `BLOCKCHAIN_PRIVATE_KEY=<LLAVE_PRIVADA_DE_TU_WALLET_SERVIDOR>` (para firmar firmas automáticas)
   * `BLOCKCHAIN_RPC_URL=https://rpc-amoy.polygon.technology`
