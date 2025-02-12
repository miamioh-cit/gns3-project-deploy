pipeline {
    agent any

    environment {
        DOCKER_CREDENTIALS_ID = 'roseaw-dockerhub'  
        DOCKER_IMAGE = 'cithit/gns3-builder'  //<-- Change this to match your DockerHub repo
        IMAGE_TAG = "build-${BUILD_NUMBER}"
        GITHUB_URL = 'https://github.com/miamioh-cit/vm-deploy.git'  //<-- Change this to your repo
        KUBECONFIG = credentials('roseaw-225')  //<-- Kubernetes credentials in Jenkins
    }

    stages {
        stage('Checkout Code') {
            steps {
                git url: "${GITHUB_URL}", branch: 'main'
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    sh "docker build -t ${DOCKER_IMAGE}:${IMAGE_TAG} ."
                }
            }
        }

        stage('Push to DockerHub') {
            steps {
                script {
                    withCredentials([usernamePassword(credentialsId: "${DOCKER_CREDENTIALS_ID}", usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                        sh "echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin"
                        sh "docker push ${DOCKER_IMAGE}:${IMAGE_TAG}"
                    }
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                script {
                    withCredentials([file(credentialsId: 'roseaw-225', variable: 'KUBECONFIG')]) {
                        def kubeConfig = readFile(KUBECONFIG)
                        writeFile file: "/tmp/kubeconfig", text: kubeConfig

                        sh """
                        export KUBECONFIG=/tmp/kubeconfig
                        echo "🔄 Updating deployment.yaml with new image: ${DOCKER_IMAGE}:${IMAGE_TAG}"
                        sed -i 's|cithit/gns3-builder:latest|${DOCKER_IMAGE}:${IMAGE_TAG}|' deployment.yaml
                        kubectl apply -f deployment.yaml
                        kubectl rollout status deployment gns3-deployment
                        """
                    }
                }
            }
        }

        stage('Run Python Script in Kubernetes') {
            steps {
                script {
                    withCredentials([file(credentialsId: 'roseaw-225', variable: 'KUBECONFIG')]) {
                        sh """
                        export KUBECONFIG=/tmp/kubeconfig
                        echo "⏳ Waiting for pod to be ready..."
                        POD_NAME=$(kubectl get pods -l app=gns3 -o jsonpath="{.items[0].metadata.name}")

                        echo "🚀 Running Python script inside container: $POD_NAME"
                        kubectl exec -it $POD_NAME -- python /app/gns3_deploy.py
                        """
                    }
                }
            }
        }
    }

    post {
        success {
            echo "✅ Deployment & Execution Successful! Image: ${DOCKER_IMAGE}:${IMAGE_TAG}"
        }
        failure {
            echo "❌ Deployment Failed!"
        }
    }
}
