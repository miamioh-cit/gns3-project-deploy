pipeline {
    agent any

    environment {
        DOCKER_CREDENTIALS_ID = 'roseaw-dockerhub'  
        DOCKER_IMAGE = 'cithit/gns3-project-deploy' 
        IMAGE_TAG = "build-${BUILD_NUMBER}"
        GITHUB_URL = 'https://github.com/miamioh-cit/gns3-project-deploy.git'
        KUBECONFIG = credentials('roseaw-225')  
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

        stage('Deploy to Dev Environment') {
            steps {
                script {
                    // Read Kubernetes configuration using the specified KUBECONFIG
                    withCredentials([file(credentialsId: 'roseaw-225', variable: 'KUBECONFIG')]) {
                        def kubeConfig = readFile(KUBECONFIG)
                        writeFile file: "/tmp/kubeconfig", text: kubeConfig
        
                        echo "🔧 Using Kubernetes config from credentials."
        
                        // Update deployment.yaml to use the new image tag
                        sh """
                        export KUBECONFIG=/tmp/kubeconfig
        
                        echo "🔄 Updating deployment.yaml with new image: ${DOCKER_IMAGE}:${IMAGE_TAG}"
                        sed -i 's|${DOCKER_IMAGE}:latest|${DOCKER_IMAGE}:${IMAGE_TAG}|' deployment.yaml
        
                        echo "🚀 Applying deployment.yaml to Kubernetes..."
                        kubectl apply -f deployment.yaml || echo "❌ Failed to apply deployment"
                    }
                }
            }
        } 
        
    }
        
    post {
        success {
            echo "✅ Deployment Successful! Image: ${DOCKER_IMAGE}:${IMAGE_TAG}"
        }
        failure {
            echo "❌ Deployment Failed!"
        }
    }
}

}
