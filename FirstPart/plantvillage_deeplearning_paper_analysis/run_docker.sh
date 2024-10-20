docker build -t caffe-tcc ./caffe
docker run -it -v $(pwd)/caffe:/TCC caffe-tcc
#docker run --runtime=nvidia --gpus all -it -v $(pwd)/caffe:/TCC caffe-tcc