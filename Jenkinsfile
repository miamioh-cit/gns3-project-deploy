pipeline {
    agent any

    environment {
        DOCKER_CREDENTIALS_ID = 'roseaw-dockerhub'  
        DOCKER_IMAGE = 'cithit/gns3-project-deploy'  //<-- Change this to match your DockerHub repo
        IMAGE_TAG = "build-${BUILD_NUMBER}"
        GITHUB_URL = 'https://github.com/miamioh-cit/vm-deploy.git'
        KUBECONFIG = credentials('roseaw-225')  
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

                        echo "📦 Pushing Docker image: ${DOCKER_IMAGE}:${IMAGE_TAG}"
                        docker push ${DOCKER_IMAGE}:${IMAGE_TAG} || exit 1
                        '''
                    }
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                script {
                    withCredentials([file(credentialsId: 'roseaw-225', variable: 'KUBECONFIG')]) {
                        sh '''
                        export KUBECONFIG=/tmp/kubeconfig
                        echo "🚀 Deploying new image to Kubernetes: ${DOCKER_IMAGE}:${IMAGE_TAG}"
                        
                        # Directly update the Kubernetes deployment image without modifying YAML
                        kubectl set image deployment/gns3-deployment gns3-container=${DOCKER_IMAGE}:${IMAGE_TAG} --record

                        # Monitor rollout status
                        kubectl rollout status deployment gns3-deployment
                        '''
                    }
                }
            }
        }

        stage('Run Python Script in Kubernetes') {
            steps {
                script {
                    withCredentials([file(credentialsId: 'roseaw-225', variable: 'KUBECONFIG')]) {
                        sh '''
                        export KUBECONFIG=/tmp/kubeconfig
                        echo "⏳ Waiting for pod to be ready..."

                        # Retry mechanism to ensure pod is ready
                        for i in {1..10}; do
                            POD_NAME=$(kubectl get pods -l app=gns3 -o jsonpath="{.items[0].metadata.name}" 2>/dev/null)
                            if [ ! -z "$POD_NAME" ]; then
                                echo "✅ Pod found: $POD_NAME"
                                break
                            fi
                            echo "⏳ Waiting for pod... Attempt $i"
                            sleep 5
                        done

                        if [ -z "$POD_NAME" ]; then
                            echo "❌ No pod found for deployment! Exiting."
                            exit 1
                        fi

                        echo "🚀 Running Python script inside container: $POD_NAME"
                        kubectl exec -it "$POD_NAME" -- python /app/gns3_deploy.py || exit 1
                        '''
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
