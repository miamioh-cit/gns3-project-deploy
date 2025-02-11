pipeline {
    agent any

    environment {
        DOCKER_CREDENTIALS_ID = 'roseaw-dockerhub'  
        DOCKER_IMAGE = 'cithit/gns3-project-deploy' 
        IMAGE_TAG = "build-${BUILD_NUMBER}"
        GITHUB_URL = 'https://github.com/miamioh-cit/gns3-project-deploy.git'
        KUBECONFIG_CRED_ID = 'roseaw-225'  
    }

    stages {
        stage('Checkout Code') {
            steps {
                git url: GITHUB_URL, branch: 'main'
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
                    withCredentials([usernamePassword(credentialsId: DOCKER_CREDENTIALS_ID, 
                                                      usernameVariable: 'DOCKER_USER', 
                                                      passwordVariable: 'DOCKER_PASS')]) {
                        sh """
                        echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin
                        docker push ${DOCKER_IMAGE}:${IMAGE_TAG}
                        """
                    }
                }
            }
        }

        stage('Deploy to Dev Environment') {
            steps {
                script {
                    withCredentials([file(credentialsId: KUBECONFIG_CRED_ID, variable: 'KUBECONFIG')]) {
                        echo "🔧 Using Kubernetes config from credentials."

                        sh """
                        export KUBECONFIG=${KUBECONFIG}

                        echo "🔄 Updating deployment.yaml with new image: ${DOCKER_IMAGE}:${IMAGE_TAG}"
                        sed -i 's|cithit/gns3-project-deploy:latest|${DOCKER_IMAGE}:${IMAGE_TAG}|' deployment.yaml

                        echo "🚀 Applying deployment.yaml to Kubernetes..."
                        kubectl apply -f deployment.yaml || echo "❌ Failed to apply deployment"

                        # Cleanup KUBECONFIG after deployment
                        rm -f ${KUBECONFIG}
                        """
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
