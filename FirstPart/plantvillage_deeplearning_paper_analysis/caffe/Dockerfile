# Pega a imagem que tem caffe instalado
# Copia diretorio atual para dentro do container
# Instala dependencias
# Executa o script que faz o setup de dados

FROM bvlc/caffe:gpu
WORKDIR /TCC
COPY . .
RUN chmod +x scripts/install_requirements.sh
RUN bash scripts/install_requirements.sh
RUN chmod +x /TCC/entrypoint.sh
#CMD ["bash", "/TCC/entrypoint.sh"]
