# Control domotico con dispositivos Tuya y Ariston
# Creamos el entorno virtual

python3 -m venv .venv  ### .venv usado por poetry y vscode

source .venv/bin/activate

pip install -r requirements.txt

# devcontainer
"postCreateCommand": "python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"


# Cifrar:
openssl enc -aes-256-cbc -salt -in archivo.txt -out archivo.enc

# Descifrar:
openssl enc -d -aes-256-cbc -in archivo.enc -out archivo.txt