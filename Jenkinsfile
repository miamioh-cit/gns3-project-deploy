pipeline {
    agent any

    environment {
        DOCKER_CREDENTIALS_ID = 'roseaw-dockerhub'  
        DOCKER_IMAGE = 'cithit/gns3-project'  
        IMAGE_TAG = "build-${BUILD_NUMBER}"
        GITHUB_URL = 'https://github.com/miamioh-cit/gns3-project-deploy.git'
    }

    stages {
        stage('Checkout Code') {
            steps {
                git url: "${GITHUB_URL}", branch: 'main'
            }
        }

        stage('Verify Deployment Files') {
            steps {
                script {
                    sh '''
                    echo "📂 Checking if deployment.yaml exists..."
                    if [ ! -f deployment.yaml ]; then
                        echo "⚠️ deployment.yaml not found! Fetching from GitHub..."
                        curl -o deployment.yaml https://raw.githubusercontent.com/miamioh-cit/vm-deploy/main/deployment.yaml
                        chmod 644 deployment.yaml  # Ensure it's writable
                    fi
                    ls -la
                    '''
                }
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
                        sh '''
                        echo "🔑 Logging into DockerHub..."
                        echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin || exit 1

                        echo "📦 Tagging Docker image as latest..."
                        docker tag ${DOCKER_IMAGE}:${IMAGE_TAG} ${DOCKER_IMAGE}:latest || exit 1

                        echo "📦 Pushing Docker image: ${DOCKER_IMAGE}:${IMAGE_TAG}"
                        docker push ${DOCKER_IMAGE}:${IMAGE_TAG} || exit 1

                        echo "📦 Pushing Docker image: ${DOCKER_IMAGE}:latest"
                        docker push ${DOCKER_IMAGE}:latest || exit 1
                        '''
                    }
                }
            }
        }

        stage('Run Docker Container Locally') {
            steps {
                script {
                    sh '''
                    echo "🚀 Stopping and Removing Existing Container..."
                    docker stop gns3-container || true
                    docker rm gns3-container || true

                    echo "🚀 Running New Docker Container Locally..."
                    docker run -d --name gns3-container -p 8080:8080 ${DOCKER_IMAGE}:${IMAGE_TAG} || exit 1

                    echo "✅ Docker container is running!"
                    '''
                }
            }
        }
    }

    post {
        success {
            script {
                echo "✅ Local Deployment Successful! Image: ${DOCKER_IMAGE}:${IMAGE_TAG}"
            }
        }
        failure {
            script {
                echo "❌ Local Deployment Failed!"
            }
        }
    }
}
