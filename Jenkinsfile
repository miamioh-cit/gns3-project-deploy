pipeline {
    agent any
    
    environment {
        DOCKERHUB_USERNAME = 'your-dockerhub-username'
        DOCKERHUB_PASSWORD = credentials('dockerhub-credentials-id')
        IMAGE_NAME = "your-dockerhub-username/gns3-builder:latest"
        KUBE_DEPLOYMENT = "gns3-deployment"
        KUBE_NAMESPACE = "default"
    }

    stages {
        stage('Checkout Code') {
            steps {
                git 'https://github.com/your-repo/your-script-repo.git'
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    sh "docker build -t $IMAGE_NAME ."
                }
            }
        }

        stage('Push to DockerHub') {
            steps {
                script {
                    sh "echo $DOCKERHUB_PASSWORD | docker login -u $DOCKERHUB_USERNAME --password-stdin"
                    sh "docker push $IMAGE_NAME"
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                script {
                    sh """
                    kubectl set image deployment/$KUBE_DEPLOYMENT gns3-container=$IMAGE_NAME -n $KUBE_NAMESPACE
                    kubectl rollout status deployment/$KUBE_DEPLOYMENT -n $KUBE_NAMESPACE
                    """
                }
            }
        }
    }
}
