cd $(dirname $0)
minikube delete
minikube start
eval $(minikube docker-env)

if [ -z $1 ];
then
    docker build -t phdi/record-linkage ../../
    export IMAGE=phdi/record-linkage
    envsubst < ../record-linkage.yml | kubectl apply -f -
else
    docker pull --platform linux/amd64 $1
    export IMAGE=$1
    envsubst < ../record-linkage.yml | kubectl apply -f -
fi

echo "\n"
echo "waiting for cluster to reconcile..."
sleep 20

minikube tunnel &> /dev/null &
sleep 5
kubectl get all