###################################################################################
#!/usr/bin/env bash


#Funcion para pedir confirmacion
confirm() {
	while true; do
		read -p "$1 (s/n): " yn
		case $yn in
			[Ss]* ) return 0;; #Para aceptar (s o S)
			[Nn]* ) echo "Saliendo..."; exit 1;; # Salir (n o N)
			* ) echo "Por favor responde con s o n";;
		esac
	done
}

###################################################################################

#Iniciar siempre desde el home
cd ~ || exit 1

###################################################################################

#Salir si un comando falla
set -e

###################################################################################

#Instalar todos los requerimientos del sistema, herramientas y librerias
echo "Instalando los requerimientos, herramientas y librerias"
confirm "¿Quieres continuar?"

sudo apt-get update && sudo apt-get install -y \
build-essential git python3 python3-pip libudev-dev gcc-arm-none-eabi libffi-dev xterm swig libpcsclite-dev python-is-python3 autoconf libtool python3-venv libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev gcc-12 g++-12

sudo update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-12 100
sudo update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-12 100

gcc --version

###################################################################################

#Clonar el repositorio, si no esta ya instalado
echo "Clonar el repositorio"
confirm "¿Quieres continuar?"

# Configurar variables
REPO_URL="https://github.com/Coldcard/firmware.git"
SIG_URL="https://github.com/Coldcard/firmware/raw/master/releases/signatures.txt"
SHA_URL="https://github.com/Coldcard/firmware/raw/master/releases/sha256sums.txt"
KEY_ID="4589779ADFC14F3327534EA8A3A31BAD5A2A5B10"
KEYSERVER="keyserver.ubuntu.com"

# Descargar archivos de firma y sumas de verificación
echo "📥 Descargando archivos de firma y sumas de comprobación..."
wget -q -O signatures.txt "$SIG_URL" || { echo "❌ Error al descargar signatures.txt"; exit 1; }
wget -q -O sha256sums.txt "$SHA_URL" || { echo "❌ Error al descargar sha256sums.txt"; exit 1; }

# Descargar e importar la clave pública
echo "🔑 Descargando e importando clave PGP $KEY_ID..."
gpg --batch --keyserver "$KEYSERVER" --recv-keys "$KEY_ID" || { echo "❌ Error al importar clave"; exit 1; }

# Verificar la firma del archivo de sumas
echo "🔍 Verificando firma del archivo de sumas..."
gpg --batch --verify signatures.txt sha256sums.txt && echo "✅ Firma válida" || { echo "❌ Firma inválida"; exit 1; }

if [ ! -d "firmware/.git" ]; then
    echo "📥 Descargando el repositorio... esto puede llevar algún tiempo, por favor ten paciencia... "
    rm -rf firmware  # Eliminar repositorio corrupto si existe
    git clone --recursive "$REPO_URL" firmware || { echo "❌ Error al descargar el repositorio"; exit 1; }
else
    echo "✅ El repositorio ya está descargado."
fi

# Verificar las sumas de los archivos en el repositorio
echo "🔍 Verificando la integridad de los archivos..."
cd firmware || { echo "❌ Error al acceder al directorio del repositorio"; exit 1; }
sha256sum -c ../sha256sums.txt --ignore-missing || { echo "❌ Error en la verificación de hash"; exit 1; }
cd ..

echo "🎉 Repositorio verificado y seguro."

###################################################################################

#Ir al directorio 
cd firmware

###################################################################################

#Aplicar parche de dirección
echo "Aplicar parche linux_addr.patch"
confirm "¿Quieres continuar?"

set +e
git apply --check unix/linux_addr.patch 2>/dev/null
if [ $? -eq 0 ]; then
    git apply unix/linux_addr.patch
    echo "Parche aplicado correctamente."
else
    echo "El parche ya estaba aplicado o no es necesario."
fi
set -e

###################################################################################

#Necesario para Ubuntu 24.04
echo "Aplicar parche ubuntu24_mpy.patch"
confirm "¿Quieres continuar?"

pushd external/micropython > /dev/null
set +e
git apply --check ../../ubuntu24_mpy.patch 2>/dev/null
if [ $? -eq 0 ]; then
    git apply ../../ubuntu24_mpy.patch
    echo "Parche ubuntu24_mpy.patch aplicado correctamente."
else
    echo "El parche ya estaba aplicado o no es necesario."
fi
set -e
popd > /dev/null

###################################################################################

#Crear y activar el entorno virtual Python
echo "Crear y activar el entorno virtual Python"
confirm "¿Quieres continuar?"

if [ ! -d "ENV" ]; then
	echo "Creando entorno virtual Python..."
	python3 -m venv ENV
else
	echo "Entorno virtual ya creado. Activando..."
	
fi

source ENV/bin/activate || { echo "Error al activar el entorno virtual"; exit 1; }


# Detener script si ocurre un error
set -e

###################################################################################

# Verificar que el entorno virtual esté activado
if [[ "$(which python)" != *ENV/bin/python ]]; then
    echo "Error: No se activó el entorno virtual. Intenta activarlo manualmente con:"
    echo "source ~/firmware/ENV/bin/activate"
    exit 1
fi

echo "Entorno virtual activado correctamente: $(which python)"

###################################################################################

# Verificar si 'numpy' está instalado, y si no lo está, instalarlo
echo "Verificar 'numpy', si no lo instala"
confirm "¿Quieres continuar?"

echo "Verificando si 'numpy' está instalado..."
if ! pip show numpy &>/dev/null; then
    echo "'numpy' no está instalado. Instalando..."
    pip install numpy
else
    echo "'numpy' ya está instalado"
fi

###################################################################################

#Instalar dependencias
echo "Instalar dependencias"
confirm "¿Quieres continuar"

#Verificar e instalar dependencias
echo "Comprobando e instalando dependencias" 
pip install --no-cache-dir -U pip setuptools pysdl2-dll

echo "Instalando dependencias de requirements.txt..."
pip install --no-cache-dir -r requirements.txt

###################################################################################

# Crear el simulador de Coldcard
echo "Crear el simulador de Coldcard"
confirm "¿Quieres continuar?"

#pushd ~/firmware/external/micropython/mpy-cross/
cd ~/firmware/external/micropython/mpy-cross/

###################################################################################

#Buscar y eliminar la opcion -Wno-error=enum-int-mismatch del Makefile
echo "Buscar el error en el makefile"
confirm "¿Quieres continuar?"

# Eliminar la opción '-Wno-error=enum-int-mismatch' del Makefile
echo "Eliminando '-Wno-error=enum-int-mismatch' del Makefile..."
sed -i '/-Wno-error=enum-int-mismatch/d' ~/firmware/external/micropython/ports/unix/Makefile

# Eliminar la opción '-Wno-error=enum-int-mismatch' del parche (si es necesario)
echo "Eliminando '-Wno-error=enum-int-mismatch' del parche ubuntu24_mpy.patch..."
sed -i '/-Wno-error=enum-int-mismatch/d' ~/firmware/ubuntu24_mpy.patch

# Eliminar la opción '-Wno-error=enum-int-mismatch' del mpy-cross
echo "Eliminando '-Wno-error=enum-int-mismatch' del Makefile..."
sed -i '/-Wno-error=enum-int-mismatch/d' ~/firmware/external/micropython/mpy-cross/Makefile

###################################################################################

#Ejecutar make
echo "Ejecutar make"
confirm "¿Quieres continuar?"

make V=1  # En mpy-cross

###################################################################################

#Ir al direccotio ~/firmware/Unix
echo "Ir al directorio ~/firmware/Unix"
confirm "¿Quieres continuar?"

cd ~/firmware/unix

###################################################################################

#Limpiar y compilar
echo "Limpiar y compilar"
confirm "¿Quieres continuar?"

make clean

###################################################################################

echo "make setup"
confirm "¿Quieres continuar?"

make setup

###################################################################################

echo "make ngu-setup"
confirm "¿Quieres continuar?"

make ngu-setup

###################################################################################

echo "make"
confirm "¿Quieres continuar?"

make

###################################################################################

#Preguntar al usuario que Coldcard quiere emular
echo "¿Que Coldcard quieres emular?"
echo "1) Mk4"
echo "2) Q1"
read -p "Elige 1 para Mk4 o 2 para Q1: " coldcard_choice

###################################################################################

#Verificando eleccion y configurando
case $coldcard_choice in
	1)
		echo "Emulando Coldcard Mk4..."
		ln -sf ../external/micropython/ports/unix/coldcard-mpy coldcard-mpy
		;;
	2)
		echo "Emulando Coldcard Q1..."
		ln -sf ../external/micropython/ports/unix/q1-mpy coldcard-mpy
		;;
	*)
		echo "Opción no valida...Configurando por defecto Coldcard Mk4..."
		ln -sf ../external/micropython/ports/unix/coldcard-mpy coldcard-mpy
		;;
esac

###################################################################################

#Damos los permisos necesarios
chmod +x simulator.py

###################################################################################

#Ejecutar el simulador en el entorno virtual activo
./simulator.py













